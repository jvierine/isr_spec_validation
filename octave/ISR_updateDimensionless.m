function p = ISR_updateDimensionless(p)
  % Octave-compatible ISRTS input normalization. The upstream code uses
  % reci' * omegai, which fails for more than one ion when omegai is an
  % ion-by-frequency matrix. Apply each ion's factor to its own row.
  k = p.radar.k;
  re = 1/(k*p.plasmas.vTe);
  p.dimensionless.thetae = re*p.plasmas.omegae;
  p.dimensionless.psien = re*p.factors.nuen;
  p.dimensionless.phie = re*p.plasmas.Oe;
  p.dimensionless.psiec_par = re*p.factors.nuei;
  p.dimensionless.psiec_perp = re*(p.factors.nuei+p.factors.nuee);

  ri = 1./(k*p.plasmas.vTi);
  p.dimensionless.thetai = bsxfun(@times, ri(:), p.plasmas.omegai);
  p.dimensionless.psiin = ri.*p.factors.nuin;
  p.dimensionless.phii = ri.*p.plasmas.Oi;
  p.dimensionless.psiic = ri.*p.factors.nuii;
end
