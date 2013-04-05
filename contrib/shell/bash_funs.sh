### Add the file in it's entirety to your ~/.bashrc
### Modify the following two lines for your local installation
BISQUE=/home/bisque
MATLAB_ROOT=/opt/matlab

bq-activate() {
  # Activate the bisque environment 
  # 
  local bq=${1:-$BISQUE}
  cd $bq
  source bqenv/bin/activate
}

bq-deactivate() {
  deactivate
}

matlab-activate() {
    local matlabroot=$MATLAB_ROOT

    OLDPATH=$PATH
    OLDLD=$LD_LIBRARY_PATH

# 
    LD_LIBRARY_PATH=$matlabroot/runtime/glnxa64:$matlabroot/bin/glnxa64:$matlabroot/sys/os/glnxa64:$matlabroot/sys/java/jre/glnxa64/jre/lib/amd64/native_threads:$matlabroot/sys/java/jre/glnxa64/jre/lib/amd64/server:$matlabroot/sys/java/jre/glnxa64/jre/lib/amd64:
    XAPPLRESDIR=$matlabroot/X11/app-defaults 

    PATH=$PATH:$matlabroot/bin:.
    export LD_LIBRARY_PATH XAPPLRESDIR
}

matlab-deactivate() {
    PATH=$OLDPATH
    LD_LIBRARY_PATH=$OLDLD
}
