/*
 * Copyright (c) 2003, 2007-11 Matteo Frigo
 * Copyright (c) 2003, 2007-11 Massachusetts Institute of Technology
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 *
 */

/* This file was automatically generated --- DO NOT EDIT */
/* Generated on Sat Apr 28 11:03:52 EDT 2012 */

#include "codelet-rdft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_r2cb.native -fma -reorder-insns -schedule-for-pipeline -compact -variables 4 -pipeline-latency 4 -sign 1 -n 8 -name r2cb_8 -include r2cb.h */

/*
 * This function contains 20 FP additions, 12 FP multiplications,
 * (or, 8 additions, 0 multiplications, 12 fused multiply/add),
 * 19 stack variables, 2 constants, and 16 memory accesses
 */
#include "r2cb.h"

static void r2cb_8(R *R0, R *R1, R *Cr, R *Ci, stride rs, stride csr, stride csi, INT v, INT ivs, INT ovs)
{
     DK(KP1_414213562, +1.414213562373095048801688724209698078569671875);
     DK(KP2_000000000, +2.000000000000000000000000000000000000000000000);
     {
	  INT i;
	  for (i = v; i > 0; i = i - 1, R0 = R0 + ovs, R1 = R1 + ovs, Cr = Cr + ivs, Ci = Ci + ivs, MAKE_VOLATILE_STRIDE(rs), MAKE_VOLATILE_STRIDE(csr), MAKE_VOLATILE_STRIDE(csi)) {
	       E Th, Tb, Tg, Ti;
	       {
		    E T4, Ta, Td, T9, T3, Tc, T8, Te;
		    T4 = Cr[WS(csr, 2)];
		    Ta = Ci[WS(csi, 2)];
		    {
			 E T1, T2, T6, T7;
			 T1 = Cr[0];
			 T2 = Cr[WS(csr, 4)];
			 T6 = Cr[WS(csr, 1)];
			 T7 = Cr[WS(csr, 3)];
			 Td = Ci[WS(csi, 1)];
			 T9 = T1 - T2;
			 T3 = T1 + T2;
			 Tc = T6 - T7;
			 T8 = T6 + T7;
			 Te = Ci[WS(csi, 3)];
		    }
		    {
			 E Tj, T5, Tk, Tf;
			 Tj = FNMS(KP2_000000000, T4, T3);
			 T5 = FMA(KP2_000000000, T4, T3);
			 Th = FMA(KP2_000000000, Ta, T9);
			 Tb = FNMS(KP2_000000000, Ta, T9);
			 Tk = Td - Te;
			 Tf = Td + Te;
			 R0[0] = FMA(KP2_000000000, T8, T5);
			 R0[WS(rs, 2)] = FNMS(KP2_000000000, T8, T5);
			 R0[WS(rs, 3)] = FMA(KP2_000000000, Tk, Tj);
			 R0[WS(rs, 1)] = FNMS(KP2_000000000, Tk, Tj);
			 Tg = Tc - Tf;
			 Ti = Tc + Tf;
		    }
	       }
	       R1[0] = FMA(KP1_414213562, Tg, Tb);
	       R1[WS(rs, 2)] = FNMS(KP1_414213562, Tg, Tb);
	       R1[WS(rs, 3)] = FMA(KP1_414213562, Ti, Th);
	       R1[WS(rs, 1)] = FNMS(KP1_414213562, Ti, Th);
	  }
     }
}

static const kr2c_desc desc = { 8, "r2cb_8", {8, 0, 12, 0}, &GENUS };

void X(codelet_r2cb_8) (planner *p) {
     X(kr2c_register) (p, r2cb_8, &desc);
}

#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_r2cb.native -compact -variables 4 -pipeline-latency 4 -sign 1 -n 8 -name r2cb_8 -include r2cb.h */

/*
 * This function contains 20 FP additions, 6 FP multiplications,
 * (or, 20 additions, 6 multiplications, 0 fused multiply/add),
 * 21 stack variables, 2 constants, and 16 memory accesses
 */
#include "r2cb.h"

static void r2cb_8(R *R0, R *R1, R *Cr, R *Ci, stride rs, stride csr, stride csi, INT v, INT ivs, INT ovs)
{
     DK(KP1_414213562, +1.414213562373095048801688724209698078569671875);
     DK(KP2_000000000, +2.000000000000000000000000000000000000000000000);
     {
	  INT i;
	  for (i = v; i > 0; i = i - 1, R0 = R0 + ovs, R1 = R1 + ovs, Cr = Cr + ivs, Ci = Ci + ivs, MAKE_VOLATILE_STRIDE(rs), MAKE_VOLATILE_STRIDE(csr), MAKE_VOLATILE_STRIDE(csi)) {
	       E T5, Tg, T3, Te, T9, Ti, Td, Tj, T6, Ta;
	       {
		    E T4, Tf, T1, T2;
		    T4 = Cr[WS(csr, 2)];
		    T5 = KP2_000000000 * T4;
		    Tf = Ci[WS(csi, 2)];
		    Tg = KP2_000000000 * Tf;
		    T1 = Cr[0];
		    T2 = Cr[WS(csr, 4)];
		    T3 = T1 + T2;
		    Te = T1 - T2;
		    {
			 E T7, T8, Tb, Tc;
			 T7 = Cr[WS(csr, 1)];
			 T8 = Cr[WS(csr, 3)];
			 T9 = KP2_000000000 * (T7 + T8);
			 Ti = T7 - T8;
			 Tb = Ci[WS(csi, 1)];
			 Tc = Ci[WS(csi, 3)];
			 Td = KP2_000000000 * (Tb - Tc);
			 Tj = Tb + Tc;
		    }
	       }
	       T6 = T3 + T5;
	       R0[WS(rs, 2)] = T6 - T9;
	       R0[0] = T6 + T9;
	       Ta = T3 - T5;
	       R0[WS(rs, 1)] = Ta - Td;
	       R0[WS(rs, 3)] = Ta + Td;
	       {
		    E Th, Tk, Tl, Tm;
		    Th = Te - Tg;
		    Tk = KP1_414213562 * (Ti - Tj);
		    R1[WS(rs, 2)] = Th - Tk;
		    R1[0] = Th + Tk;
		    Tl = Te + Tg;
		    Tm = KP1_414213562 * (Ti + Tj);
		    R1[WS(rs, 1)] = Tl - Tm;
		    R1[WS(rs, 3)] = Tl + Tm;
	       }
	  }
     }
}

static const kr2c_desc desc = { 8, "r2cb_8", {20, 6, 0, 0}, &GENUS };

void X(codelet_r2cb_8) (planner *p) {
     X(kr2c_register) (p, r2cb_8, &desc);
}

#endif				/* HAVE_FMA */
