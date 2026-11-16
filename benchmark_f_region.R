# Native R/C Virtanen kernel timing. Run with taskset -c 0 on avaruus.
library(hdf5r)
root <- normalizePath('.')
upstream <- file.path(root, '.cache/ISspectrum')
dyn.load(file.path(root, '.cache/virtanen-native/ISspectrum.so'))
for (file in c('cerfexp.R','pldfas.R','pldf.R','pldfvv.R','specCalc.R','ISspectrum.general.R'))
  source(file.path(upstream, 'R', file))
src <- H5File$new('tables/expanded/f_region_440.2MHz.h5', mode='r')
f <- src[['frequency_hz']][]
reference <- src[['Virtanen/S_total']][]
src$close_all()
run <- function() {
  result <- ISspectrum.general(ele=c(1e11,2000,0,0),
    ion=list(c(16,1e11,1000,0,0)), fradar=440.2e6,
    scattAngle=180, freq=f)
  result * (2*pi/(9.978688e-29*1e11))
}
result <- run() # warm up the native kernel
err <- max(abs(result-reference))/max(abs(result),abs(reference))
stopifnot(is.finite(err), err <= 1e-6)
elapsed <- numeric(7)
for (i in seq_along(elapsed)) {
  start <- as.numeric(Sys.time())
  for (j in 1:100) value <- run()
  elapsed[i] <- (as.numeric(Sys.time()) - start)/100
  stopifnot(max(abs(value-result))/max(abs(result)) <= 1e-9)
}
stopifnot(all(is.finite(elapsed)), all(elapsed > 0))
dst <- H5File$new('tables/speed_virtanen.h5', mode='w')
g <- dst$create_group('Virtanen')
g[['elapsed_s']] <- elapsed
h5attr(g,'median_elapsed_s') <- median(elapsed)
h5attr(g,'min_elapsed_s') <- min(elapsed)
h5attr(g,'max_elapsed_s') <- max(elapsed)
h5attr(g,'error_vs_saved') <- err
h5attr(dst,'host') <- 'avaruus'
h5attr(dst,'threads_per_call') <- 1L
h5attr(dst,'cpu_affinity') <- '0'
h5attr(dst,'r_version') <- R.version.string
h5attr(dst,'timing_scope') <- 'full spectrum function; 1 warm-up; median of 7 batches of 100 calls divided by 100; no startup or HDF5 I/O'
dst$close_all()
cat('Virtanen',median(elapsed),err,'\n')
