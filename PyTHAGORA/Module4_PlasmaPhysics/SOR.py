"""
#EE 411 Spring 2007
#Original Author: (c) Victor P. Pasko, Ph.D., Penn State University
#email: vpasko@psu.edu

# [f,it]=sor(a,b,c,d,f,s,w,epsilon,nx,ny,dnorms) solves
# five-point dufference equation for f(ix,iy) with constant coefficents a,b,c and d:
#
# a*f(ix,iy-1)+b*f(ix,iy+1)+c*f(ix-1,iy)+d*f(ix+1,iy)+f(ix,iy)=s(ix,iy)

# The solution is obtained in a domain consisting of nx+1 by ny+1 grid ponts.
# The boundary values of f (i.e., at ix=1, ix=nx+1, iy=1:ny+1; and iy=1, iy=ny+1,ix=1:nx+1)
# should be specified in matrix f before calling the function,
# and values of f inside of the domain (ix=2:nx, iy=2:ny)
# are obtained by successive overrelaxation (SOR) technique.

# w is a relaxation factor (1<w<2). The best value is
# w=2/(1+sqrt(1-rho_sor^2)), where in the case of
# the two-dimensional Poisson equation in the square (nx=ny)
# rho_sor=cos(pi/nx).

# epsilon - desired accuracy of the solution.
# A good approximation for dnorms is dnorms=sum(sum(s.^2))

#Reference: Hockney, R. W. and J. W. Eastwood, Computer simulation using particles,
#McGraw-Hill, 1981, pages 174-181

Adapted to Python from MATLAB by Seth Gerow, Embry-Riddle Aeronautical University
"""
import numpy as np

def sor(a,b,c,d,f,s,w,epsilon,nx,ny,dnorms):
    it=0 #number of iterations
    while 1:
        it=it+1
        dnorm=0
        for ix in range(2,nx):
            for iy in range(2,ny):
                residual=a*f[ix,iy-1] + b*f[ix,iy+1] + c*f[ix-1,iy] + d*f[ix+1,iy] + f[ix,iy]-s[ix,iy];
                dnorm=dnorm+residual**2
                f[ix, iy]=f[ix, iy]-w*residual
        if dnorm/dnorms < epsilon:
            break
        if it>10000:
            raise RecursionError('Solution has not been reached in 10000 iterations.')
            break
    return it, f