/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_SINGULARITY_BOOST_H
#define _LINUX_SINGULARITY_BOOST_H
#include <linux/devfreq.h>
#ifdef CONFIG_SINGULARITY_BUS_BOOST
void singularity_bus_register(struct devfreq *df, unsigned int index);
void singularity_bus_unregister(struct devfreq *df);
void singularity_bus_kick(void);
unsigned long singularity_devfreq_floor(struct devfreq *df);
#else
static inline void singularity_bus_register(struct devfreq *df, unsigned int index) {}
static inline void singularity_bus_unregister(struct devfreq *df) {}
static inline void singularity_bus_kick(void) {}
static inline unsigned long singularity_devfreq_floor(struct devfreq *df) {return 0;}
#endif
#endif
