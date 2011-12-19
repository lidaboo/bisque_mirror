/***************************************************************************
 *   Copyright (C) 2008 by Center for Bio-Image Informatics UCSB           *
 *                                                                         *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/
package bisque;
public class BQError{
	
	public static String error;
	public static boolean isError;
	
	public static String getLastError(){ return error; }
	public static void setLastError(Exception cause){
		error = "ERROR";
		if(!isError){
            error += "::MESSAGE:" + cause.getMessage();
            error += "::TRACE:";
			StackTraceElement elements[] = cause.getStackTrace();
			for ( int i=0, n=elements.length; i < n; i++ )
				error += 	elements[i].toString() + ";==> " ;
			System.out.println(error);
		}
	}
	public static void help(){
		System.out.println("---------------------------------------------");
		System.out.println("BQError class:");
		System.out.println("---------------------------------------------");
		System.out.println("BQError.getLastError()");
		System.out.println("---------------------------------------------");
	}
}