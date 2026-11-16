function loaded = libisloaded(~)
  % GUISDAP spec.m calls MATLAB's library probe. Under Octave use its native
  % MATLAB branch, which evaluates the same formulas without the C library.
  loaded = false;
end
