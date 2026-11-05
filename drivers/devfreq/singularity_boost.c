// SPDX-License-Identifier: GPL-2.0
/* Singularity: temporary bandwidth votes without changing struct devfreq ABI. */
#include <linux/singularity_boost.h>
#include <linux/input.h>
#include <linux/jiffies.h>
#include <linux/msm_drm_notify.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/workqueue.h>

static struct devfreq *bus_devices[2];
static const unsigned long bus_floors[2] = {3879, 4577};
static DEFINE_MUTEX(bus_registry_lock);
static unsigned long input_expires, wake_expires;
static bool screen_on = true, boost_ready;

static unsigned long singularity_floor_value(unsigned long now, bool on,
 unsigned long input_end, unsigned long wake_end, unsigned long floor)
{
 if (!on)
  return 0;
 if (wake_end && time_before(now, wake_end))
  return ULONG_MAX;
 if (input_end && time_before(now, input_end))
  return floor;
 return 0;
}

unsigned long singularity_devfreq_floor(struct devfreq *df)
{
 unsigned int i;
 if (!READ_ONCE(boost_ready))
  return 0;
 for (i = 0; i < ARRAY_SIZE(bus_devices); i++)
  if (READ_ONCE(bus_devices[i]) == df)
   return singularity_floor_value(jiffies, READ_ONCE(screen_on),
    READ_ONCE(input_expires), READ_ONCE(wake_expires), bus_floors[i]);
 return 0;
}

static void bus_boost_worker(struct work_struct *work);
static DECLARE_DELAYED_WORK(bus_boost_work, bus_boost_worker);

static void bus_boost_worker(struct work_struct *work)
{
 unsigned long now, input_end, wake_end, delay = ULONG_MAX;
 unsigned int i;
 now = jiffies;
 input_end = READ_ONCE(input_expires);
 wake_end = READ_ONCE(wake_expires);
 if (READ_ONCE(screen_on)) {
  if (input_end && time_before(now, input_end))
   delay = input_end - now;
  if (wake_end && time_before(now, wake_end))
   delay = min(delay, wake_end - now);
 }
 mutex_lock(&bus_registry_lock);
 for (i = 0; i < ARRAY_SIZE(bus_devices); i++) {
  struct devfreq *df = bus_devices[i];
  if (!df)
   continue;
  mutex_lock(&df->lock);
  update_devfreq(df);
  mutex_unlock(&df->lock);
 }
 mutex_unlock(&bus_registry_lock);
 if (delay != ULONG_MAX)
  queue_delayed_work(system_freezable_wq, &bus_boost_work, max(1UL, delay));
}

void singularity_bus_register(struct devfreq *df, unsigned int index)
{
 if (index >= ARRAY_SIZE(bus_devices))
  return;
 mutex_lock(&bus_registry_lock);
 WRITE_ONCE(bus_devices[index], df);
 mutex_unlock(&bus_registry_lock);
}

void singularity_bus_unregister(struct devfreq *df)
{
 unsigned int i;
 /* Worker holds this lock while dereferencing each registered device. */
 mutex_lock(&bus_registry_lock);
 for (i = 0; i < ARRAY_SIZE(bus_devices); i++)
  if (bus_devices[i] == df)
   WRITE_ONCE(bus_devices[i], NULL);
 mutex_unlock(&bus_registry_lock);
}

static void extend_vote(unsigned long *expiry, unsigned int duration_ms)
{
 unsigned long old, end = jiffies + msecs_to_jiffies(duration_ms);
 do {
  old = READ_ONCE(*expiry);
  if (old && !time_after(end, old))
   return;
 } while (cmpxchg(expiry, old, end) != old);
}

void singularity_bus_kick(void)
{
 if (!READ_ONCE(boost_ready) || !READ_ONCE(screen_on))
  return;
 extend_vote(&input_expires, 64);
 mod_delayed_work(system_freezable_wq, &bus_boost_work, 0);
}

static int bus_display_event(struct notifier_block *nb, unsigned long event, void *data)
{
 struct msm_drm_notifier *notification = data;
 int blank;
 if (event != MSM_DRM_EARLY_EVENT_BLANK || !notification || !notification->data)
  return NOTIFY_OK;
 blank = *(int *)notification->data;
 WRITE_ONCE(screen_on, blank == MSM_DRM_BLANK_UNBLANK);
 if (blank == MSM_DRM_BLANK_UNBLANK)
  extend_vote(&wake_expires, 1000);
 else {
  WRITE_ONCE(input_expires, 0);
  WRITE_ONCE(wake_expires, 0);
 }
 mod_delayed_work(system_freezable_wq, &bus_boost_work, 0);
 return NOTIFY_OK;
}
static struct notifier_block bus_display_notifier = {.notifier_call = bus_display_event};

static void bus_input_event(struct input_handle *handle, unsigned int type, unsigned int code, int value)
{
 if (type == EV_SYN && code == SYN_REPORT)
  singularity_bus_kick();
}
static int bus_input_connect(struct input_handler *handler, struct input_dev *dev,
 const struct input_device_id *id)
{
 struct input_handle *handle;
 int ret;
 handle = kzalloc(sizeof(*handle), GFP_KERNEL);
 if (!handle)
  return -ENOMEM;
 handle->dev = dev;
 handle->handler = handler;
 handle->name = "singularity_bus";
 ret = input_register_handle(handle);
 if (ret)
  goto free;
 ret = input_open_device(handle);
 if (ret) {
  input_unregister_handle(handle);
  goto free;
 }
 return 0;
free:
 kfree(handle);
 return ret;
}
static void bus_input_disconnect(struct input_handle *handle)
{
 input_close_device(handle);
 input_unregister_handle(handle);
 kfree(handle);
}
static const struct input_device_id bus_input_ids[] = {
 {.flags = INPUT_DEVICE_ID_MATCH_EVBIT | INPUT_DEVICE_ID_MATCH_ABSBIT,
  .evbit = {BIT_MASK(EV_ABS)},
  .absbit = {[BIT_WORD(ABS_MT_POSITION_X)] = BIT_MASK(ABS_MT_POSITION_X) | BIT_MASK(ABS_MT_POSITION_Y)}},
 {}
};
static struct input_handler bus_input_handler = {
 .event = bus_input_event, .connect = bus_input_connect,
 .disconnect = bus_input_disconnect, .name = "singularity_bus", .id_table = bus_input_ids
};
static int __init singularity_bus_init(void)
{
 int ret = input_register_handler(&bus_input_handler);
 if (ret)
  return ret;
 ret = msm_drm_register_client(&bus_display_notifier);
 if (ret) {
  input_unregister_handler(&bus_input_handler);
  return ret;
 }
 WRITE_ONCE(boost_ready, true);
 return 0;
}
late_initcall(singularity_bus_init);
