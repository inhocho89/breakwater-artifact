/*
 * dg_config.h - Dagor configurations
 */

#pragma once

/* Recommended parameters with 1,000 clinets
*  in XL170 environment
* - Memcached : 25
* - 1 us average service time
* (bimod) #define DAGOR_OVERLOAD_THRESH		20
* (exp) #define DAGOR_OVERLOAD_THRESH		30
* (const) #define DAGOR_OVERLOAD_THRESH		30
*
* - 10 us average service time
* (bimod) #define DAGOR_OVERLOAD_THRESH		80
* (exp) #define DAGOR_OVERLOAD_THRESH		70
* (const) #define DAGOR_OVERLOAD_THRESH		60
*
* - 100 us average service time
* (bimod) #define DAGOR_OVERLOAD_THRESH		500
* (exp) #define DAGOR_OVERLOAD_THRESH		500
* (const) #define DAGOR_OVERLOAD_THRESH		500
*/

/* delay threshold to detect congestion */
#define DAGOR_OVERLOAD_THRESH	70	// in us
/* max priority update interval */
#define DAGOR_PRIO_UPDATE_INT	1000	// in us
/* max # requests for priority update */
#define DAGOR_PRIO_UPDATE_REQS	2000	// in # reqs
/* queueing delay monitor interval */
#define DAGOR_PRIO_MONITOR	10
/* decrement factor when congested */
#define DAGOR_ALPHA		0.95
/* increment factor when uncongested */
#define DAGOR_BETA		0.01

#define CDG_BATCH_WAIT_US	0
