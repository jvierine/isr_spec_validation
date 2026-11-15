function [mi, qi] = analysisIon(ion)
  % Input-mass adapter for Sandbem/ISRTS; no spectral equation is changed.
  global adapter_mass_kg adapter_charge_c;
  assert(numel(ion) == numel(adapter_mass_kg));
  % ISR_init transposes these outputs. Return columns so its stored masses
  % and charges are rows, matching the ion-fraction row in ISRTS.
  mi = adapter_mass_kg(:);
  qi = adapter_charge_c*ones(size(mi));
end
