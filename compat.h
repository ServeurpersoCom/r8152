/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Backport of the mainline r8152 driver to older kernels: kernel APIs
 * that the mainline source uses and that older kernels lack or spell
 * differently. Included by r8152.c after all kernel headers.
 */
#ifndef R8152_COMPAT_H
#define R8152_COMPAT_H

#include <linux/version.h>
#include <linux/iopoll.h>

/* Added in v6.18 */
#ifndef poll_timeout_us
#define poll_timeout_us(op, cond, sleep_us, timeout_us, sleep_before_op) \
({ \
	u64 __timeout_us = (timeout_us); \
	unsigned long __sleep_us = (sleep_us); \
	ktime_t __timeout = ktime_add_us(ktime_get(), __timeout_us); \
	int ___ret; \
	might_sleep_if((__sleep_us) != 0); \
	if ((sleep_before_op) && __sleep_us) \
		usleep_range((__sleep_us >> 2) + 1, __sleep_us); \
	for (;;) { \
		bool __expired = __timeout_us && \
			ktime_compare(ktime_get(), __timeout) > 0; \
		/* guarantee 'op' and 'cond' are evaluated after timeout expired */ \
		barrier(); \
		op; \
		if (cond) { \
			___ret = 0; \
			break; \
		} \
		if (__expired) { \
			___ret = -ETIMEDOUT; \
			break; \
		} \
		if (__sleep_us) \
			usleep_range((__sleep_us >> 2) + 1, __sleep_us); \
		cpu_relax(); \
	} \
	___ret; \
})
#endif

/* v6.16 switched the address argument to struct sockaddr_storage */
#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 16, 0)
#define dev_set_mac_address(dev, ss, extack) \
	dev_set_mac_address(dev, (struct sockaddr *)(ss), extack)
#endif

/* v7.4 made the module owner implicit */
#if LINUX_VERSION_CODE < KERNEL_VERSION(7, 4, 0)
#define usb_register_device_driver(drv) \
	usb_register_device_driver(drv, THIS_MODULE)
#endif

/*
 * Mainline drivers carry no version, and DKMS only replaces a module whose
 * version sorts above the in-tree one (v1.12.13 in v6.12).
 */
MODULE_VERSION("v7.4-rc4");

#endif
