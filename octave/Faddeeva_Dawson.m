function y = Faddeeva_Dawson(z)
  % ISR_Model ships only MATLAB MEX binaries. For its real collisionless
  % arguments, Octave's built-in Dawson function is the same special function.
  assert(all(imag(z(:)) == 0));
  y = dawson(real(z));
end
