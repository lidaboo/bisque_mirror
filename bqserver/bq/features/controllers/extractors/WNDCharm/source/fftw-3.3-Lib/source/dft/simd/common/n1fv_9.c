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
/* Generated on Sat Apr 28 11:00:01 EDT 2012 */

#include "codelet-dft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_notw_c.native -fma -reorder-insns -schedule-for-pipeline -simd -compact -variables 4 -pipeline-latency 8 -n 9 -name n1fv_9 -include n1f.h */

/*
 * This function contains 46 FP additions, 38 FP multiplications,
 * (or, 12 additions, 4 multiplications, 34 fused multiply/add),
 * 68 stack variables, 19 constants, and 18 memory accesses
 */
#include "n1f.h"

static void n1fv_9(const R *ri, const R *ii, R *ro, R *io, stride is, stride os, INT v, INT ivs, INT ovs)
{
     DVK(KP939692620, +0.939692620785908384054109277324731469936208134);
     DVK(KP826351822, +0.826351822333069651148283373230685203999624323);
     DVK(KP879385241, +0.879385241571816768108218554649462939872416269);
     DVK(KP984807753, +0.984807753012208059366743024589523013670643252);
     DVK(KP666666666, +0.666666666666666666666666666666666666666666667);
     DVK(KP852868531, +0.852868531952443209628250963940074071936020296);
     DVK(KP907603734, +0.907603734547952313649323976213898122064543220);
     DVK(KP420276625, +0.420276625461206169731530603237061658838781920);
     DVK(KP673648177, +0.673648177666930348851716626769314796000375677);
     DVK(KP898197570, +0.898197570222573798468955502359086394667167570);
     DVK(KP347296355, +0.347296355333860697703433253538629592000751354);
     DVK(KP866025403, +0.866025403784438646763723170752936183471402627);
     DVK(KP439692620, +0.439692620785908384054109277324731469936208134);
     DVK(KP203604859, +0.203604859554852403062088995281827210665664861);
     DVK(KP152703644, +0.152703644666139302296566746461370407999248646);
     DVK(KP586256827, +0.586256827714544512072145703099641959914944179);
     DVK(KP968908795, +0.968908795874236621082202410917456709164223497);
     DVK(KP726681596, +0.726681596905677465811651808188092531873167623);
     DVK(KP500000000, +0.500000000000000000000000000000000000000000000);
     {
	  INT i;
	  const R *xi;
	  R *xo;
	  xi = ri;
	  xo = ro;
	  for (i = v; i > 0; i = i - VL, xi = xi + (VL * ivs), xo = xo + (VL * ovs), MAKE_VOLATILE_STRIDE(is), MAKE_VOLATILE_STRIDE(os)) {
	       V T1, T2, T3, T6, Tb, T7, T8, Tc, Td, Tv, T4;
	       T1 = LD(&(xi[0]), ivs, &(xi[0]));
	       T2 = LD(&(xi[WS(is, 3)]), ivs, &(xi[WS(is, 1)]));
	       T3 = LD(&(xi[WS(is, 6)]), ivs, &(xi[0]));
	       T6 = LD(&(xi[WS(is, 1)]), ivs, &(xi[WS(is, 1)]));
	       Tb = LD(&(xi[WS(is, 2)]), ivs, &(xi[0]));
	       T7 = LD(&(xi[WS(is, 4)]), ivs, &(xi[0]));
	       T8 = LD(&(xi[WS(is, 7)]), ivs, &(xi[WS(is, 1)]));
	       Tc = LD(&(xi[WS(is, 5)]), ivs, &(xi[WS(is, 1)]));
	       Td = LD(&(xi[WS(is, 8)]), ivs, &(xi[0]));
	       Tv = VSUB(T3, T2);
	       T4 = VADD(T2, T3);
	       {
		    V Tl, T9, Tm, Te, Tj, T5;
		    Tl = VSUB(T7, T8);
		    T9 = VADD(T7, T8);
		    Tm = VSUB(Td, Tc);
		    Te = VADD(Tc, Td);
		    Tj = VFNMS(LDK(KP500000000), T4, T1);
		    T5 = VADD(T1, T4);
		    {
			 V Tn, Ta, Tk, Tf;
			 Tn = VFNMS(LDK(KP500000000), T9, T6);
			 Ta = VADD(T6, T9);
			 Tk = VFNMS(LDK(KP500000000), Te, Tb);
			 Tf = VADD(Tb, Te);
			 {
			      V Ty, TC, To, TB, Tx, Ts, Tg, Ti;
			      Ty = VFNMS(LDK(KP726681596), Tl, Tn);
			      TC = VFMA(LDK(KP968908795), Tn, Tl);
			      To = VFNMS(LDK(KP586256827), Tn, Tm);
			      TB = VFNMS(LDK(KP152703644), Tm, Tk);
			      Tx = VFMA(LDK(KP203604859), Tk, Tm);
			      Ts = VFNMS(LDK(KP439692620), Tl, Tk);
			      Tg = VADD(Ta, Tf);
			      Ti = VMUL(LDK(KP866025403), VSUB(Tf, Ta));
			      {
				   V Tz, TI, TF, TD, Tt, Th, Tq, Tp;
				   Tp = VFNMS(LDK(KP347296355), To, Tl);
				   Tz = VFMA(LDK(KP898197570), Ty, Tx);
				   TI = VFNMS(LDK(KP898197570), Ty, Tx);
				   TF = VFNMS(LDK(KP673648177), TC, TB);
				   TD = VFMA(LDK(KP673648177), TC, TB);
				   Tt = VFNMS(LDK(KP420276625), Ts, Tm);
				   ST(&(xo[0]), VADD(T5, Tg), ovs, &(xo[0]));
				   Th = VFNMS(LDK(KP500000000), Tg, T5);
				   Tq = VFNMS(LDK(KP907603734), Tp, Tk);
				   {
					V TA, TJ, TE, TG, Tu, Tr, TK, TH, Tw;
					TA = VFMA(LDK(KP852868531), Tz, Tj);
					TJ = VFMA(LDK(KP666666666), TD, TI);
					TE = VMUL(LDK(KP984807753), VFNMS(LDK(KP879385241), Tv, TD));
					TG = VFNMS(LDK(KP500000000), Tz, TF);
					Tu = VFNMS(LDK(KP826351822), Tt, Tn);
					ST(&(xo[WS(os, 6)]), VFNMSI(Ti, Th), ovs, &(xo[0]));
					ST(&(xo[WS(os, 3)]), VFMAI(Ti, Th), ovs, &(xo[WS(os, 1)]));
					Tr = VFNMS(LDK(KP939692620), Tq, Tj);
					TK = VMUL(LDK(KP866025403), VFMA(LDK(KP852868531), TJ, Tv));
					ST(&(xo[WS(os, 8)]), VFMAI(TE, TA), ovs, &(xo[0]));
					ST(&(xo[WS(os, 1)]), VFNMSI(TE, TA), ovs, &(xo[WS(os, 1)]));
					TH = VFMA(LDK(KP852868531), TG, Tj);
					Tw = VMUL(LDK(KP984807753), VFMA(LDK(KP879385241), Tv, Tu));
					ST(&(xo[WS(os, 4)]), VFMAI(TK, TH), ovs, &(xo[0]));
					ST(&(xo[WS(os, 5)]), VFNMSI(TK, TH), ovs, &(xo[WS(os, 1)]));
					ST(&(xo[WS(os, 7)]), VFMAI(Tw, Tr), ovs, &(xo[WS(os, 1)]));
					ST(&(xo[WS(os, 2)]), VFNMSI(Tw, Tr), ovs, &(xo[0]));
				   }
			      }
			 }
		    }
	       }
	  }
     }
     VLEAVE();
}

static const kdft_desc desc = { 9, XSIMD_STRING("n1fv_9"), {12, 4, 34, 0}, &GENUS, 0, 0, 0, 0 };

void XSIMD(codelet_n1fv_9) (planner *p) {
     X(kdft_register) (p, n1fv_9, &desc);
}

#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_notw_c.native -simd -compact -variables 4 -pipeline-latency 8 -n 9 -name n1fv_9 -include n1f.h */

/*
 * This function contains 46 FP additions, 26 FP multiplications,
 * (or, 30 additions, 10 multiplications, 16 fused multiply/add),
 * 41 stack variables, 14 constants, and 18 memory accesses
 */
#include "n1f.h"

static void n1fv_9(const R *ri, const R *ii, R *ro, R *io, stride is, stride os, INT v, INT ivs, INT ovs)
{
     DVK(KP342020143, +0.342020143325668733044099614682259580763083368);
     DVK(KP813797681, +0.813797681349373692844693217248393223289101568);
     DVK(KP939692620, +0.939692620785908384054109277324731469936208134);
     DVK(KP296198132, +0.296198132726023843175338011893050938967728390);
     DVK(KP642787609, +0.642787609686539326322643409907263432907559884);
     DVK(KP663413948, +0.663413948168938396205421319635891297216863310);
     DVK(KP556670399, +0.556670399226419366452912952047023132968291906);
     DVK(KP766044443, +0.766044443118978035202392650555416673935832457);
     DVK(KP984807753, +0.984807753012208059366743024589523013670643252);
     DVK(KP150383733, +0.150383733180435296639271897612501926072238258);
     DVK(KP852868531, +0.852868531952443209628250963940074071936020296);
     DVK(KP173648177, +0.173648177666930348851716626769314796000375677);
     DVK(KP500000000, +0.500000000000000000000000000000000000000000000);
     DVK(KP866025403, +0.866025403784438646763723170752936183471402627);
     {
	  INT i;
	  const R *xi;
	  R *xo;
	  xi = ri;
	  xo = ro;
	  for (i = v; i > 0; i = i - VL, xi = xi + (VL * ivs), xo = xo + (VL * ovs), MAKE_VOLATILE_STRIDE(is), MAKE_VOLATILE_STRIDE(os)) {
	       V T5, Ts, Tj, To, Tf, Tn, Tp, Tu, Tl, Ta, Tk, Tm, Tt;
	       {
		    V T1, T2, T3, T4;
		    T1 = LD(&(xi[0]), ivs, &(xi[0]));
		    T2 = LD(&(xi[WS(is, 3)]), ivs, &(xi[WS(is, 1)]));
		    T3 = LD(&(xi[WS(is, 6)]), ivs, &(xi[0]));
		    T4 = VADD(T2, T3);
		    T5 = VADD(T1, T4);
		    Ts = VMUL(LDK(KP866025403), VSUB(T3, T2));
		    Tj = VFNMS(LDK(KP500000000), T4, T1);
	       }
	       {
		    V Tb, Te, Tc, Td;
		    Tb = LD(&(xi[WS(is, 2)]), ivs, &(xi[0]));
		    Tc = LD(&(xi[WS(is, 5)]), ivs, &(xi[WS(is, 1)]));
		    Td = LD(&(xi[WS(is, 8)]), ivs, &(xi[0]));
		    Te = VADD(Tc, Td);
		    To = VSUB(Td, Tc);
		    Tf = VADD(Tb, Te);
		    Tn = VFNMS(LDK(KP500000000), Te, Tb);
		    Tp = VFMA(LDK(KP173648177), Tn, VMUL(LDK(KP852868531), To));
		    Tu = VFNMS(LDK(KP984807753), Tn, VMUL(LDK(KP150383733), To));
	       }
	       {
		    V T6, T9, T7, T8;
		    T6 = LD(&(xi[WS(is, 1)]), ivs, &(xi[WS(is, 1)]));
		    T7 = LD(&(xi[WS(is, 4)]), ivs, &(xi[0]));
		    T8 = LD(&(xi[WS(is, 7)]), ivs, &(xi[WS(is, 1)]));
		    T9 = VADD(T7, T8);
		    Tl = VSUB(T8, T7);
		    Ta = VADD(T6, T9);
		    Tk = VFNMS(LDK(KP500000000), T9, T6);
		    Tm = VFMA(LDK(KP766044443), Tk, VMUL(LDK(KP556670399), Tl));
		    Tt = VFNMS(LDK(KP642787609), Tk, VMUL(LDK(KP663413948), Tl));
	       }
	       {
		    V Ti, Tg, Th, Tz, TA;
		    Ti = VBYI(VMUL(LDK(KP866025403), VSUB(Tf, Ta)));
		    Tg = VADD(Ta, Tf);
		    Th = VFNMS(LDK(KP500000000), Tg, T5);
		    ST(&(xo[0]), VADD(T5, Tg), ovs, &(xo[0]));
		    ST(&(xo[WS(os, 3)]), VADD(Th, Ti), ovs, &(xo[WS(os, 1)]));
		    ST(&(xo[WS(os, 6)]), VSUB(Th, Ti), ovs, &(xo[0]));
		    Tz = VFMA(LDK(KP173648177), Tk, VFNMS(LDK(KP296198132), To, VFNMS(LDK(KP939692620), Tn, VFNMS(LDK(KP852868531), Tl, Tj))));
		    TA = VBYI(VSUB(VFNMS(LDK(KP342020143), Tn, VFNMS(LDK(KP150383733), Tl, VFNMS(LDK(KP984807753), Tk, VMUL(LDK(KP813797681), To)))), Ts));
		    ST(&(xo[WS(os, 7)]), VSUB(Tz, TA), ovs, &(xo[WS(os, 1)]));
		    ST(&(xo[WS(os, 2)]), VADD(Tz, TA), ovs, &(xo[0]));
		    {
			 V Tr, Tx, Tw, Ty, Tq, Tv;
			 Tq = VADD(Tm, Tp);
			 Tr = VADD(Tj, Tq);
			 Tx = VFMA(LDK(KP866025403), VSUB(Tt, Tu), VFNMS(LDK(KP500000000), Tq, Tj));
			 Tv = VADD(Tt, Tu);
			 Tw = VBYI(VADD(Ts, Tv));
			 Ty = VBYI(VADD(Ts, VFNMS(LDK(KP500000000), Tv, VMUL(LDK(KP866025403), VSUB(Tp, Tm)))));
			 ST(&(xo[WS(os, 8)]), VSUB(Tr, Tw), ovs, &(xo[0]));
			 ST(&(xo[WS(os, 4)]), VADD(Tx, Ty), ovs, &(xo[0]));
			 ST(&(xo[WS(os, 1)]), VADD(Tw, Tr), ovs, &(xo[WS(os, 1)]));
			 ST(&(xo[WS(os, 5)]), VSUB(Tx, Ty), ovs, &(xo[WS(os, 1)]));
		    }
	       }
	  }
     }
     VLEAVE();
}

static const kdft_desc desc = { 9, XSIMD_STRING("n1fv_9"), {30, 10, 16, 0}, &GENUS, 0, 0, 0, 0 };

void XSIMD(codelet_n1fv_9) (planner *p) {
     X(kdft_register) (p, n1fv_9, &desc);
}

#endif				/* HAVE_FMA */
