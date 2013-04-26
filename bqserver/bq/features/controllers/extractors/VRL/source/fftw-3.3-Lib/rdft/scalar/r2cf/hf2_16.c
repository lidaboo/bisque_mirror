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
/* Generated on Sat Apr 28 11:02:55 EDT 2012 */

#include "codelet-rdft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_hc2hc.native -fma -reorder-insns -schedule-for-pipeline -compact -variables 4 -pipeline-latency 4 -twiddle-log3 -precompute-twiddles -n 16 -dit -name hf2_16 -include hf.h */

/*
 * This function contains 196 FP additions, 134 FP multiplications,
 * (or, 104 additions, 42 multiplications, 92 fused multiply/add),
 * 106 stack variables, 3 constants, and 64 memory accesses
 */
#include "hf.h"

static void hf2_16(R *cr, R *ci, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DK(KP923879532, +0.923879532511286756128183189396788286822416626);
     DK(KP414213562, +0.414213562373095048801688724209698078569671875);
     DK(KP707106781, +0.707106781186547524400844362104849039284835938);
     {
	  INT m;
	  for (m = mb, W = W + ((mb - 1) * 8); m < me; m = m + 1, cr = cr + ms, ci = ci - ms, W = W + 8, MAKE_VOLATILE_STRIDE(rs)) {
	       E T35, T32;
	       {
		    E T2, Tf, TM, TO, T3, Tg, TN, TS, T4, Tp, T6, T5, Th;
		    T2 = W[0];
		    Tf = W[2];
		    TM = W[6];
		    TO = W[7];
		    T3 = W[4];
		    Tg = T2 * Tf;
		    TN = T2 * TM;
		    TS = T2 * TO;
		    T4 = T2 * T3;
		    Tp = Tf * T3;
		    T6 = W[5];
		    T5 = W[1];
		    Th = W[3];
		    {
			 E TZ, Te, T1U, T3A, T3M, T2w, T1G, T2I, T3h, T1R, T2D, T2B, T3i, Tx, T3L;
			 E T1Z, T3w, TL, T21, T26, T38, T1d, T2h, T2s, T3c, T1s, T2t, T2m, T3d, TX;
			 E T10, TV, T2a, TY, T2b;
			 {
			      E TF, TP, TT, Tq, TW, Tz, Tu, TI, TC, T1m, T1f, T1p, T1j, Tr, Ts;
			      E Tv, To, T1W;
			      {
				   E Ti, Tm, T1L, T1O, T1D, T1A, T1x, T2G, T1F, T2F;
				   {
					E T1, T7, Tb, T3z, T8, T1z, T9, Tc;
					{
					     E T1i, T1e, T1C, T1y, Tt, Ta, Tl;
					     T1 = cr[0];
					     Tt = Tf * T6;
					     Ta = T2 * T6;
					     T7 = FMA(T5, T6, T4);
					     TF = FNMS(T5, T6, T4);
					     TP = FMA(T5, TO, TN);
					     TT = FNMS(T5, TM, TS);
					     Tq = FNMS(Th, T6, Tp);
					     TW = FMA(Th, T6, Tp);
					     Tz = FMA(T5, Th, Tg);
					     Ti = FNMS(T5, Th, Tg);
					     Tl = T2 * Th;
					     Tu = FMA(Th, T3, Tt);
					     TZ = FNMS(Th, T3, Tt);
					     TI = FMA(T5, T3, Ta);
					     Tb = FNMS(T5, T3, Ta);
					     T1i = Ti * T6;
					     T1e = Ti * T3;
					     T1C = Tz * T6;
					     T1y = Tz * T3;
					     Tm = FMA(T5, Tf, Tl);
					     TC = FNMS(T5, Tf, Tl);
					     T3z = ci[0];
					     T8 = cr[WS(rs, 8)];
					     T1m = FNMS(Tm, T6, T1e);
					     T1f = FMA(Tm, T6, T1e);
					     T1p = FMA(Tm, T3, T1i);
					     T1j = FNMS(Tm, T3, T1i);
					     T1L = FNMS(TC, T6, T1y);
					     T1z = FMA(TC, T6, T1y);
					     T1O = FMA(TC, T3, T1C);
					     T1D = FNMS(TC, T3, T1C);
					     T9 = T7 * T8;
					     Tc = ci[WS(rs, 8)];
					}
					{
					     E T1u, T1w, T1v, T2E, T3y, T1B, T1E, Td, T3x;
					     T1u = cr[WS(rs, 15)];
					     T1w = ci[WS(rs, 15)];
					     T1A = cr[WS(rs, 7)];
					     Td = FMA(Tb, Tc, T9);
					     T3x = T7 * Tc;
					     T1v = TM * T1u;
					     T2E = TM * T1w;
					     Te = T1 + Td;
					     T1U = T1 - Td;
					     T3y = FNMS(Tb, T8, T3x);
					     T1B = T1z * T1A;
					     T1E = ci[WS(rs, 7)];
					     T1x = FMA(TO, T1w, T1v);
					     T3A = T3y + T3z;
					     T3M = T3z - T3y;
					     T2G = T1z * T1E;
					     T1F = FMA(T1D, T1E, T1B);
					     T2F = FNMS(TO, T1u, T2E);
					}
				   }
				   {
					E T1H, T1I, T1J, T1M, T1P, T2H;
					T1H = cr[WS(rs, 3)];
					T2H = FNMS(T1D, T1A, T2G);
					T2w = T1x - T1F;
					T1G = T1x + T1F;
					T1I = Tf * T1H;
					T2I = T2F - T2H;
					T3h = T2F + T2H;
					T1J = ci[WS(rs, 3)];
					T1M = cr[WS(rs, 11)];
					T1P = ci[WS(rs, 11)];
					{
					     E Tj, Tk, Tn, T1V;
					     {
						  E T1K, T2y, T1Q, T2A, T2x, T1N, T2z;
						  Tj = cr[WS(rs, 4)];
						  T1K = FMA(Th, T1J, T1I);
						  T2x = Tf * T1J;
						  T1N = T1L * T1M;
						  T2z = T1L * T1P;
						  Tk = Ti * Tj;
						  T2y = FNMS(Th, T1H, T2x);
						  T1Q = FMA(T1O, T1P, T1N);
						  T2A = FNMS(T1O, T1M, T2z);
						  Tn = ci[WS(rs, 4)];
						  Tr = cr[WS(rs, 12)];
						  T1R = T1K + T1Q;
						  T2D = T1Q - T1K;
						  T2B = T2y - T2A;
						  T3i = T2y + T2A;
						  T1V = Ti * Tn;
						  Ts = Tq * Tr;
						  Tv = ci[WS(rs, 12)];
					     }
					     To = FMA(Tm, Tn, Tk);
					     T1W = FNMS(Tm, Tj, T1V);
					}
				   }
			      }
			      {
				   E T19, T1b, T18, T2p, T1a, T2q;
				   {
					E TE, T23, TK, T25;
					{
					     E TA, TD, TB, T22, TG, TJ, TH, T24, T1Y, Tw, T1X;
					     TA = cr[WS(rs, 2)];
					     Tw = FMA(Tu, Tv, Ts);
					     T1X = Tq * Tv;
					     TD = ci[WS(rs, 2)];
					     TB = Tz * TA;
					     Tx = To + Tw;
					     T3L = To - Tw;
					     T1Y = FNMS(Tu, Tr, T1X);
					     T22 = Tz * TD;
					     TG = cr[WS(rs, 10)];
					     TJ = ci[WS(rs, 10)];
					     T1Z = T1W - T1Y;
					     T3w = T1W + T1Y;
					     TH = TF * TG;
					     T24 = TF * TJ;
					     TE = FMA(TC, TD, TB);
					     T23 = FNMS(TC, TA, T22);
					     TK = FMA(TI, TJ, TH);
					     T25 = FNMS(TI, TG, T24);
					}
					{
					     E T15, T17, T16, T2o;
					     T15 = cr[WS(rs, 1)];
					     T17 = ci[WS(rs, 1)];
					     TL = TE + TK;
					     T21 = TE - TK;
					     T26 = T23 - T25;
					     T38 = T23 + T25;
					     T16 = T2 * T15;
					     T2o = T2 * T17;
					     T19 = cr[WS(rs, 9)];
					     T1b = ci[WS(rs, 9)];
					     T18 = FMA(T5, T17, T16);
					     T2p = FNMS(T5, T15, T2o);
					     T1a = T3 * T19;
					     T2q = T3 * T1b;
					}
				   }
				   {
					E T1n, T1q, T1l, T2j, T1o, T2k;
					{
					     E T1g, T1k, T1h, T2i, T1c, T2r;
					     T1g = cr[WS(rs, 5)];
					     T1k = ci[WS(rs, 5)];
					     T1c = FMA(T6, T1b, T1a);
					     T2r = FNMS(T6, T19, T2q);
					     T1h = T1f * T1g;
					     T2i = T1f * T1k;
					     T1d = T18 + T1c;
					     T2h = T18 - T1c;
					     T2s = T2p - T2r;
					     T3c = T2p + T2r;
					     T1n = cr[WS(rs, 13)];
					     T1q = ci[WS(rs, 13)];
					     T1l = FMA(T1j, T1k, T1h);
					     T2j = FNMS(T1j, T1g, T2i);
					     T1o = T1m * T1n;
					     T2k = T1m * T1q;
					}
					{
					     E TQ, TU, TR, T29, T1r, T2l;
					     TQ = cr[WS(rs, 14)];
					     TU = ci[WS(rs, 14)];
					     T1r = FMA(T1p, T1q, T1o);
					     T2l = FNMS(T1p, T1n, T2k);
					     TR = TP * TQ;
					     T29 = TP * TU;
					     T1s = T1l + T1r;
					     T2t = T1l - T1r;
					     T2m = T2j - T2l;
					     T3d = T2j + T2l;
					     TX = cr[WS(rs, 6)];
					     T10 = ci[WS(rs, 6)];
					     TV = FMA(TT, TU, TR);
					     T2a = FNMS(TT, TQ, T29);
					     TY = TW * TX;
					     T2b = TW * T10;
					}
				   }
			      }
			 }
			 {
			      E T36, T3G, T3b, T3g, T28, T2d, T3F, T39, T3j, T3q, T3C, T3e, T3u, T3t;
			      {
				   E T3D, T1T, T3r, T14, T3E, T3s;
				   {
					E Ty, T3B, T11, T2c, T13, T3v;
					T36 = Te - Tx;
					Ty = Te + Tx;
					T3B = T3w + T3A;
					T3G = T3A - T3w;
					T11 = FMA(TZ, T10, TY);
					T2c = FNMS(TZ, TX, T2b);
					{
					     E T1t, T1S, T12, T37;
					     T3b = T1d - T1s;
					     T1t = T1d + T1s;
					     T1S = T1G + T1R;
					     T3g = T1G - T1R;
					     T12 = TV + T11;
					     T28 = TV - T11;
					     T2d = T2a - T2c;
					     T37 = T2a + T2c;
					     T3D = T1S - T1t;
					     T1T = T1t + T1S;
					     T13 = TL + T12;
					     T3F = TL - T12;
					     T39 = T37 - T38;
					     T3v = T38 + T37;
					}
					T3j = T3h - T3i;
					T3r = T3h + T3i;
					T3q = Ty - T13;
					T14 = Ty + T13;
					T3E = T3B - T3v;
					T3C = T3v + T3B;
					T3s = T3c + T3d;
					T3e = T3c - T3d;
				   }
				   ci[WS(rs, 7)] = T14 - T1T;
				   cr[WS(rs, 12)] = T3D - T3E;
				   ci[WS(rs, 11)] = T3D + T3E;
				   T3u = T3s + T3r;
				   T3t = T3r - T3s;
				   cr[0] = T14 + T1T;
			      }
			      {
				   E T3m, T3a, T3J, T3H;
				   ci[WS(rs, 15)] = T3u + T3C;
				   cr[WS(rs, 8)] = T3u - T3C;
				   ci[WS(rs, 3)] = T3q + T3t;
				   cr[WS(rs, 4)] = T3q - T3t;
				   T3m = T36 + T39;
				   T3a = T36 - T39;
				   T3J = T3G - T3F;
				   T3H = T3F + T3G;
				   {
					E T2Q, T20, T3N, T3T, T2C, T2J, T3U, T2f, T33, T30, T2V, T2W, T3O, T2T, T2N;
					E T2v;
					{
					     E T2R, T27, T2e, T2S;
					     {
						  E T3n, T3f, T3o, T3k;
						  T2Q = T1U + T1Z;
						  T20 = T1U - T1Z;
						  T3n = T3b - T3e;
						  T3f = T3b + T3e;
						  T3o = T3g + T3j;
						  T3k = T3g - T3j;
						  T3N = T3L + T3M;
						  T3T = T3M - T3L;
						  {
						       E T3p, T3K, T3I, T3l;
						       T3p = T3n + T3o;
						       T3K = T3o - T3n;
						       T3I = T3k - T3f;
						       T3l = T3f + T3k;
						       ci[WS(rs, 1)] = FMA(KP707106781, T3p, T3m);
						       cr[WS(rs, 6)] = FNMS(KP707106781, T3p, T3m);
						       ci[WS(rs, 13)] = FMA(KP707106781, T3K, T3J);
						       cr[WS(rs, 10)] = FMS(KP707106781, T3K, T3J);
						       ci[WS(rs, 9)] = FMA(KP707106781, T3I, T3H);
						       cr[WS(rs, 14)] = FMS(KP707106781, T3I, T3H);
						       cr[WS(rs, 2)] = FMA(KP707106781, T3l, T3a);
						       ci[WS(rs, 5)] = FNMS(KP707106781, T3l, T3a);
						       T2R = T21 + T26;
						       T27 = T21 - T26;
						       T2e = T28 + T2d;
						       T2S = T28 - T2d;
						  }
					     }
					     {
						  E T2Y, T2Z, T2n, T2u;
						  T2C = T2w - T2B;
						  T2Y = T2w + T2B;
						  T2Z = T2I + T2D;
						  T2J = T2D - T2I;
						  T3U = T2e - T27;
						  T2f = T27 + T2e;
						  T33 = FMA(KP414213562, T2Y, T2Z);
						  T30 = FNMS(KP414213562, T2Z, T2Y);
						  T2V = T2h + T2m;
						  T2n = T2h - T2m;
						  T2u = T2s + T2t;
						  T2W = T2s - T2t;
						  T3O = T2R - T2S;
						  T2T = T2R + T2S;
						  T2N = FMA(KP414213562, T2n, T2u);
						  T2v = FNMS(KP414213562, T2u, T2n);
					     }
					}
					{
					     E T2M, T3S, T31, T2P, T3Q, T3R, T3P, T2U;
					     {
						  E T2g, T2X, T2O, T2K, T3V, T3X, T3W, T34, T2L, T3Y;
						  T2M = FNMS(KP707106781, T2f, T20);
						  T2g = FMA(KP707106781, T2f, T20);
						  T34 = FNMS(KP414213562, T2V, T2W);
						  T2X = FMA(KP414213562, T2W, T2V);
						  T2O = FMA(KP414213562, T2C, T2J);
						  T2K = FNMS(KP414213562, T2J, T2C);
						  T3V = FMA(KP707106781, T3U, T3T);
						  T3X = FNMS(KP707106781, T3U, T3T);
						  T35 = T33 - T34;
						  T3W = T34 + T33;
						  T3S = T2K - T2v;
						  T2L = T2v + T2K;
						  T3Y = T30 - T2X;
						  T31 = T2X + T30;
						  ci[WS(rs, 14)] = FMA(KP923879532, T3W, T3V);
						  cr[WS(rs, 9)] = FMS(KP923879532, T3W, T3V);
						  ci[0] = FMA(KP923879532, T2L, T2g);
						  cr[WS(rs, 7)] = FNMS(KP923879532, T2L, T2g);
						  cr[WS(rs, 13)] = FMS(KP923879532, T3Y, T3X);
						  ci[WS(rs, 10)] = FMA(KP923879532, T3Y, T3X);
						  T2P = T2N + T2O;
						  T3Q = T2O - T2N;
					     }
					     T32 = FNMS(KP707106781, T2T, T2Q);
					     T2U = FMA(KP707106781, T2T, T2Q);
					     T3R = FNMS(KP707106781, T3O, T3N);
					     T3P = FMA(KP707106781, T3O, T3N);
					     cr[WS(rs, 3)] = FMA(KP923879532, T2P, T2M);
					     ci[WS(rs, 4)] = FNMS(KP923879532, T2P, T2M);
					     cr[WS(rs, 1)] = FMA(KP923879532, T31, T2U);
					     ci[WS(rs, 6)] = FNMS(KP923879532, T31, T2U);
					     ci[WS(rs, 8)] = FMA(KP923879532, T3Q, T3P);
					     cr[WS(rs, 15)] = FMS(KP923879532, T3Q, T3P);
					     ci[WS(rs, 12)] = FMA(KP923879532, T3S, T3R);
					     cr[WS(rs, 11)] = FMS(KP923879532, T3S, T3R);
					}
				   }
			      }
			 }
		    }
	       }
	       ci[WS(rs, 2)] = FMA(KP923879532, T35, T32);
	       cr[WS(rs, 5)] = FNMS(KP923879532, T35, T32);
	  }
     }
}

static const tw_instr twinstr[] = {
     {TW_CEXP, 1, 1},
     {TW_CEXP, 1, 3},
     {TW_CEXP, 1, 9},
     {TW_CEXP, 1, 15},
     {TW_NEXT, 1, 0}
};

static const hc2hc_desc desc = { 16, "hf2_16", twinstr, &GENUS, {104, 42, 92, 0} };

void X(codelet_hf2_16) (planner *p) {
     X(khc2hc_register) (p, hf2_16, &desc);
}
#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_hc2hc.native -compact -variables 4 -pipeline-latency 4 -twiddle-log3 -precompute-twiddles -n 16 -dit -name hf2_16 -include hf.h */

/*
 * This function contains 196 FP additions, 108 FP multiplications,
 * (or, 156 additions, 68 multiplications, 40 fused multiply/add),
 * 82 stack variables, 3 constants, and 64 memory accesses
 */
#include "hf.h"

static void hf2_16(R *cr, R *ci, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DK(KP382683432, +0.382683432365089771728459984030398866761344562);
     DK(KP923879532, +0.923879532511286756128183189396788286822416626);
     DK(KP707106781, +0.707106781186547524400844362104849039284835938);
     {
	  INT m;
	  for (m = mb, W = W + ((mb - 1) * 8); m < me; m = m + 1, cr = cr + ms, ci = ci - ms, W = W + 8, MAKE_VOLATILE_STRIDE(rs)) {
	       E T2, T5, Tg, Ti, Tk, To, TE, TC, T6, T3, T8, TW, TJ, Tt, TU;
	       E Tc, Tx, TH, TN, TO, TP, TR, T1f, T1k, T1b, T1i, T1y, T1H, T1u, T1F;
	       {
		    E T7, Tv, Ta, Ts, T4, Tw, Tb, Tr;
		    {
			 E Th, Tn, Tj, Tm;
			 T2 = W[0];
			 T5 = W[1];
			 Tg = W[2];
			 Ti = W[3];
			 Th = T2 * Tg;
			 Tn = T5 * Tg;
			 Tj = T5 * Ti;
			 Tm = T2 * Ti;
			 Tk = Th - Tj;
			 To = Tm + Tn;
			 TE = Tm - Tn;
			 TC = Th + Tj;
			 T6 = W[5];
			 T7 = T5 * T6;
			 Tv = Tg * T6;
			 Ta = T2 * T6;
			 Ts = Ti * T6;
			 T3 = W[4];
			 T4 = T2 * T3;
			 Tw = Ti * T3;
			 Tb = T5 * T3;
			 Tr = Tg * T3;
		    }
		    T8 = T4 + T7;
		    TW = Tv - Tw;
		    TJ = Ta + Tb;
		    Tt = Tr - Ts;
		    TU = Tr + Ts;
		    Tc = Ta - Tb;
		    Tx = Tv + Tw;
		    TH = T4 - T7;
		    TN = W[6];
		    TO = W[7];
		    TP = FMA(T2, TN, T5 * TO);
		    TR = FNMS(T5, TN, T2 * TO);
		    {
			 E T1d, T1e, T19, T1a;
			 T1d = Tk * T6;
			 T1e = To * T3;
			 T1f = T1d - T1e;
			 T1k = T1d + T1e;
			 T19 = Tk * T3;
			 T1a = To * T6;
			 T1b = T19 + T1a;
			 T1i = T19 - T1a;
		    }
		    {
			 E T1w, T1x, T1s, T1t;
			 T1w = TC * T6;
			 T1x = TE * T3;
			 T1y = T1w - T1x;
			 T1H = T1w + T1x;
			 T1s = TC * T3;
			 T1t = TE * T6;
			 T1u = T1s + T1t;
			 T1F = T1s - T1t;
		    }
	       }
	       {
		    E Tf, T3s, T1N, T3e, TA, T3r, T1Q, T3b, TM, T2N, T1W, T2w, TZ, T2M, T21;
		    E T2x, T1B, T1K, T2V, T2W, T2X, T2Y, T2j, T2E, T2o, T2D, T18, T1n, T2Q, T2R;
		    E T2S, T2T, T28, T2B, T2d, T2A;
		    {
			 E T1, T3d, Te, T3c, T9, Td;
			 T1 = cr[0];
			 T3d = ci[0];
			 T9 = cr[WS(rs, 8)];
			 Td = ci[WS(rs, 8)];
			 Te = FMA(T8, T9, Tc * Td);
			 T3c = FNMS(Tc, T9, T8 * Td);
			 Tf = T1 + Te;
			 T3s = T3d - T3c;
			 T1N = T1 - Te;
			 T3e = T3c + T3d;
		    }
		    {
			 E Tq, T1O, Tz, T1P;
			 {
			      E Tl, Tp, Tu, Ty;
			      Tl = cr[WS(rs, 4)];
			      Tp = ci[WS(rs, 4)];
			      Tq = FMA(Tk, Tl, To * Tp);
			      T1O = FNMS(To, Tl, Tk * Tp);
			      Tu = cr[WS(rs, 12)];
			      Ty = ci[WS(rs, 12)];
			      Tz = FMA(Tt, Tu, Tx * Ty);
			      T1P = FNMS(Tx, Tu, Tt * Ty);
			 }
			 TA = Tq + Tz;
			 T3r = Tq - Tz;
			 T1Q = T1O - T1P;
			 T3b = T1O + T1P;
		    }
		    {
			 E TG, T1T, TL, T1U, T1S, T1V;
			 {
			      E TD, TF, TI, TK;
			      TD = cr[WS(rs, 2)];
			      TF = ci[WS(rs, 2)];
			      TG = FMA(TC, TD, TE * TF);
			      T1T = FNMS(TE, TD, TC * TF);
			      TI = cr[WS(rs, 10)];
			      TK = ci[WS(rs, 10)];
			      TL = FMA(TH, TI, TJ * TK);
			      T1U = FNMS(TJ, TI, TH * TK);
			 }
			 TM = TG + TL;
			 T2N = T1T + T1U;
			 T1S = TG - TL;
			 T1V = T1T - T1U;
			 T1W = T1S - T1V;
			 T2w = T1S + T1V;
		    }
		    {
			 E TT, T1Y, TY, T1Z, T1X, T20;
			 {
			      E TQ, TS, TV, TX;
			      TQ = cr[WS(rs, 14)];
			      TS = ci[WS(rs, 14)];
			      TT = FMA(TP, TQ, TR * TS);
			      T1Y = FNMS(TR, TQ, TP * TS);
			      TV = cr[WS(rs, 6)];
			      TX = ci[WS(rs, 6)];
			      TY = FMA(TU, TV, TW * TX);
			      T1Z = FNMS(TW, TV, TU * TX);
			 }
			 TZ = TT + TY;
			 T2M = T1Y + T1Z;
			 T1X = TT - TY;
			 T20 = T1Y - T1Z;
			 T21 = T1X + T20;
			 T2x = T1X - T20;
		    }
		    {
			 E T1r, T2f, T1J, T2m, T1A, T2g, T1E, T2l;
			 {
			      E T1p, T1q, T1G, T1I;
			      T1p = cr[WS(rs, 15)];
			      T1q = ci[WS(rs, 15)];
			      T1r = FMA(TN, T1p, TO * T1q);
			      T2f = FNMS(TO, T1p, TN * T1q);
			      T1G = cr[WS(rs, 11)];
			      T1I = ci[WS(rs, 11)];
			      T1J = FMA(T1F, T1G, T1H * T1I);
			      T2m = FNMS(T1H, T1G, T1F * T1I);
			 }
			 {
			      E T1v, T1z, T1C, T1D;
			      T1v = cr[WS(rs, 7)];
			      T1z = ci[WS(rs, 7)];
			      T1A = FMA(T1u, T1v, T1y * T1z);
			      T2g = FNMS(T1y, T1v, T1u * T1z);
			      T1C = cr[WS(rs, 3)];
			      T1D = ci[WS(rs, 3)];
			      T1E = FMA(Tg, T1C, Ti * T1D);
			      T2l = FNMS(Ti, T1C, Tg * T1D);
			 }
			 T1B = T1r + T1A;
			 T1K = T1E + T1J;
			 T2V = T1B - T1K;
			 T2W = T2f + T2g;
			 T2X = T2l + T2m;
			 T2Y = T2W - T2X;
			 {
			      E T2h, T2i, T2k, T2n;
			      T2h = T2f - T2g;
			      T2i = T1E - T1J;
			      T2j = T2h + T2i;
			      T2E = T2h - T2i;
			      T2k = T1r - T1A;
			      T2n = T2l - T2m;
			      T2o = T2k - T2n;
			      T2D = T2k + T2n;
			 }
		    }
		    {
			 E T14, T29, T1m, T26, T17, T2a, T1h, T25;
			 {
			      E T12, T13, T1j, T1l;
			      T12 = cr[WS(rs, 1)];
			      T13 = ci[WS(rs, 1)];
			      T14 = FMA(T2, T12, T5 * T13);
			      T29 = FNMS(T5, T12, T2 * T13);
			      T1j = cr[WS(rs, 13)];
			      T1l = ci[WS(rs, 13)];
			      T1m = FMA(T1i, T1j, T1k * T1l);
			      T26 = FNMS(T1k, T1j, T1i * T1l);
			 }
			 {
			      E T15, T16, T1c, T1g;
			      T15 = cr[WS(rs, 9)];
			      T16 = ci[WS(rs, 9)];
			      T17 = FMA(T3, T15, T6 * T16);
			      T2a = FNMS(T6, T15, T3 * T16);
			      T1c = cr[WS(rs, 5)];
			      T1g = ci[WS(rs, 5)];
			      T1h = FMA(T1b, T1c, T1f * T1g);
			      T25 = FNMS(T1f, T1c, T1b * T1g);
			 }
			 T18 = T14 + T17;
			 T1n = T1h + T1m;
			 T2Q = T18 - T1n;
			 T2R = T29 + T2a;
			 T2S = T25 + T26;
			 T2T = T2R - T2S;
			 {
			      E T24, T27, T2b, T2c;
			      T24 = T14 - T17;
			      T27 = T25 - T26;
			      T28 = T24 - T27;
			      T2B = T24 + T27;
			      T2b = T29 - T2a;
			      T2c = T1h - T1m;
			      T2d = T2b + T2c;
			      T2A = T2b - T2c;
			 }
		    }
		    {
			 E T23, T2r, T3u, T3w, T2q, T3v, T2u, T3p;
			 {
			      E T1R, T22, T3q, T3t;
			      T1R = T1N - T1Q;
			      T22 = KP707106781 * (T1W + T21);
			      T23 = T1R + T22;
			      T2r = T1R - T22;
			      T3q = KP707106781 * (T2w - T2x);
			      T3t = T3r + T3s;
			      T3u = T3q + T3t;
			      T3w = T3t - T3q;
			 }
			 {
			      E T2e, T2p, T2s, T2t;
			      T2e = FNMS(KP382683432, T2d, KP923879532 * T28);
			      T2p = FMA(KP382683432, T2j, KP923879532 * T2o);
			      T2q = T2e + T2p;
			      T3v = T2p - T2e;
			      T2s = FMA(KP923879532, T2d, KP382683432 * T28);
			      T2t = FNMS(KP923879532, T2j, KP382683432 * T2o);
			      T2u = T2s + T2t;
			      T3p = T2t - T2s;
			 }
			 cr[WS(rs, 7)] = T23 - T2q;
			 cr[WS(rs, 11)] = T3v - T3w;
			 ci[WS(rs, 12)] = T3v + T3w;
			 ci[0] = T23 + T2q;
			 ci[WS(rs, 4)] = T2r - T2u;
			 cr[WS(rs, 15)] = T3p - T3u;
			 ci[WS(rs, 8)] = T3p + T3u;
			 cr[WS(rs, 3)] = T2r + T2u;
		    }
		    {
			 E T11, T35, T3g, T3i, T1M, T3h, T38, T39;
			 {
			      E TB, T10, T3a, T3f;
			      TB = Tf + TA;
			      T10 = TM + TZ;
			      T11 = TB + T10;
			      T35 = TB - T10;
			      T3a = T2N + T2M;
			      T3f = T3b + T3e;
			      T3g = T3a + T3f;
			      T3i = T3f - T3a;
			 }
			 {
			      E T1o, T1L, T36, T37;
			      T1o = T18 + T1n;
			      T1L = T1B + T1K;
			      T1M = T1o + T1L;
			      T3h = T1L - T1o;
			      T36 = T2W + T2X;
			      T37 = T2R + T2S;
			      T38 = T36 - T37;
			      T39 = T37 + T36;
			 }
			 ci[WS(rs, 7)] = T11 - T1M;
			 cr[WS(rs, 12)] = T3h - T3i;
			 ci[WS(rs, 11)] = T3h + T3i;
			 cr[0] = T11 + T1M;
			 cr[WS(rs, 4)] = T35 - T38;
			 cr[WS(rs, 8)] = T39 - T3g;
			 ci[WS(rs, 15)] = T39 + T3g;
			 ci[WS(rs, 3)] = T35 + T38;
		    }
		    {
			 E T2z, T2H, T3A, T3C, T2G, T3B, T2K, T3x;
			 {
			      E T2v, T2y, T3y, T3z;
			      T2v = T1N + T1Q;
			      T2y = KP707106781 * (T2w + T2x);
			      T2z = T2v + T2y;
			      T2H = T2v - T2y;
			      T3y = KP707106781 * (T21 - T1W);
			      T3z = T3s - T3r;
			      T3A = T3y + T3z;
			      T3C = T3z - T3y;
			 }
			 {
			      E T2C, T2F, T2I, T2J;
			      T2C = FMA(KP382683432, T2A, KP923879532 * T2B);
			      T2F = FNMS(KP382683432, T2E, KP923879532 * T2D);
			      T2G = T2C + T2F;
			      T3B = T2F - T2C;
			      T2I = FNMS(KP923879532, T2A, KP382683432 * T2B);
			      T2J = FMA(KP923879532, T2E, KP382683432 * T2D);
			      T2K = T2I + T2J;
			      T3x = T2J - T2I;
			 }
			 ci[WS(rs, 6)] = T2z - T2G;
			 cr[WS(rs, 13)] = T3B - T3C;
			 ci[WS(rs, 10)] = T3B + T3C;
			 cr[WS(rs, 1)] = T2z + T2G;
			 cr[WS(rs, 5)] = T2H - T2K;
			 cr[WS(rs, 9)] = T3x - T3A;
			 ci[WS(rs, 14)] = T3x + T3A;
			 ci[WS(rs, 2)] = T2H + T2K;
		    }
		    {
			 E T2P, T31, T3m, T3o, T30, T3j, T34, T3n;
			 {
			      E T2L, T2O, T3k, T3l;
			      T2L = Tf - TA;
			      T2O = T2M - T2N;
			      T2P = T2L - T2O;
			      T31 = T2L + T2O;
			      T3k = TM - TZ;
			      T3l = T3e - T3b;
			      T3m = T3k + T3l;
			      T3o = T3l - T3k;
			 }
			 {
			      E T2U, T2Z, T32, T33;
			      T2U = T2Q + T2T;
			      T2Z = T2V - T2Y;
			      T30 = KP707106781 * (T2U + T2Z);
			      T3j = KP707106781 * (T2Z - T2U);
			      T32 = T2Q - T2T;
			      T33 = T2V + T2Y;
			      T34 = KP707106781 * (T32 + T33);
			      T3n = KP707106781 * (T33 - T32);
			 }
			 ci[WS(rs, 5)] = T2P - T30;
			 cr[WS(rs, 10)] = T3n - T3o;
			 ci[WS(rs, 13)] = T3n + T3o;
			 cr[WS(rs, 2)] = T2P + T30;
			 cr[WS(rs, 6)] = T31 - T34;
			 cr[WS(rs, 14)] = T3j - T3m;
			 ci[WS(rs, 9)] = T3j + T3m;
			 ci[WS(rs, 1)] = T31 + T34;
		    }
	       }
	  }
     }
}

static const tw_instr twinstr[] = {
     {TW_CEXP, 1, 1},
     {TW_CEXP, 1, 3},
     {TW_CEXP, 1, 9},
     {TW_CEXP, 1, 15},
     {TW_NEXT, 1, 0}
};

static const hc2hc_desc desc = { 16, "hf2_16", twinstr, &GENUS, {156, 68, 40, 0} };

void X(codelet_hf2_16) (planner *p) {
     X(khc2hc_register) (p, hf2_16, &desc);
}
#endif				/* HAVE_FMA */
