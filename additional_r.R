# R interpreter + the unmodified ISspectrum C kernel. All outputs are HDF5.
library(hdf5r)
root <- normalizePath('.')
upstream <- file.path(root,'.cache/ISspectrum')
lib <- file.path(root,'.cache/virtanen-native',paste0('ISspectrum',.Platform$dynlib.ext))
dyn.load(lib)
for (file in c('cerfexp.R','pldfas.R','pldf.R','pldfvv.R','specCalc.R','ISspectrum.general.R')) {
  source(file.path(upstream,'R',file))
}
sha <- function(path) strsplit(system2('shasum',c('-a','256',shQuote(path)),stdout=TRUE),' ')[[1]][1]
revision <- system2('git',c('-C',shQuote(upstream),'rev-parse','HEAD'),stdout=TRUE)
src <- H5File$new('.cache/additional_inputs.h5',mode='r')
dst <- H5File$new('.cache/additional_r.h5',mode='w')
for (name in names(src[['cases']])) {
  q <- src[[paste0('cases/',name)]]
  container <- dst$create_group(name)
  out <- container$create_group('Virtanen')
  h5attr(out,'git_commit') <- revision
  h5attr(out,'code_sha256') <- sha(file.path(upstream,'R/ISspectrum.general.R'))
  h5attr(out,'native_code_sha256') <- sha(file.path(upstream,'src/spec_worker.c'))
  h5attr(out,'adapter_sha256') <- sha('additional_r.R')
  h5attr(out,'r_version') <- R.version.string
  h5attr(out,'native_build') <- 'cc -O2 -dynamiclib spec_worker.c transf_worker.c -lm (macOS); no upstream source edits'
  if (h5attr(q,'B_T')!=0 && h5attr(q,'angle_k_B_deg')!=0) {
    h5attr(out,'status') <- 'unsupported'
    h5attr(out,'reason') <- 'No oblique magnetic response; parallel Maxwellian case is identical to the unmagnetized response.'
    next
  }
  tryCatch({
    ne <- h5attr(q,'ne_m3'); te <- h5attr(q,'te_K'); ti <- h5attr(q,'ti_K')
    mass <- q[['ion_masses_u']][]; frac <- q[['ion_fractions']][]; f <- q[['frequency_hz']][]
    ions <- lapply(seq_along(mass),function(i) c(mass[i],ne*frac[i],ti,h5attr(q,'nu_in_s_1'),0))
    ele <- c(ne,te,h5attr(q,'nu_en_s_1'),0)
    # Convert the documented angular-frequency cross-section density to a
    # per-electron PSD per Hz. This is fixed by the source, not fitted to data.
    s <- ISspectrum.general(ele=ele,ion=ions,fradar=h5attr(q,'f_r_MHz')*1e6,scattAngle=180,freq=f)
    s <- s*(2*pi/(9.978688e-29*ne))
    stopifnot(all(is.finite(s)),length(s)==length(f))
    out[['S_total']] <- s
    h5attr(out,'status') <- 'computed'
    cat(name,'Virtanen computed\n')
  }, error=function(e) {
    h5attr(out,'status') <- 'error'; h5attr(out,'reason') <- conditionMessage(e)
    cat(name,'Virtanen',conditionMessage(e),'\n')
  })
}
src$close_all(); dst$close_all()
