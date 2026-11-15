function S_total = octave_kernel(code, d)
  f = reshape(d.frequency_hz, 1, []);
  masses = reshape(d.ion_masses_u, 1, []);
  fractions = reshape(d.ion_fractions, 1, []);
  codes = reshape(d.ion_codes, 1, []);
  names = {'O+', 'NO+', 'O2+', 'N2+', 'H+', 'He+', 'N+'};
  ion = names(codes);
  assert(abs(sum(fractions)-1) < 1e-12);
  if strcmp(code, 'Martinez')
    config = init_ISR_simulator(d.radar_hz, min(f), max(f), numel(f));
    % The native constructor assumes an evenly spaced grid. Preserve the
    % requested frequencies, including the disjoint plasma-line windows.
    config.frequency = f;
    config.omega = 2*pi*f;
    for j = 1:numel(ion)
      [config, idx] = addSpecie_ISR_simulator(config, ion{j});
      % Built-in species masses are nominal; use the prescribed case mass.
      config.species.m_s(idx) = masses(j)*d.amu;
    end
    config = changeSpecie_ISR_simulator(config, 'E-', d.ne, d.te, 0);
    for j = 1:numel(ion)
      config = changeSpecie_ISR_simulator(config, ion{j}, d.ne*fractions(j), d.ti, 0);
    end
    density_psd_per_hz = ISR_simulator(config);
  else
    % ISRTS normally maps names to fixed nominal masses (and labels N2+/O2+
    % as doubly charged). Supply the prescribed singly charged ions through
    % a local input adapter; the spectral routines are left unchanged.
    global adapter_mass_kg adapter_charge_c;
    adapter_mass_kg = masses*d.amu;
    adapter_charge_c = d.e;
    factors = struct();
    magnetic = d.B > 0;
    collisional = d.nu_e > 0 || d.nu_i > 0;
    factors.mode = double([0, collisional, magnetic, 0]);
    factors.nu = [d.nu_e, repmat(d.nu_i, 1, numel(ion))];
    factors.B = [d.B, d.theta];
    factors.gordmode = 2;
    if isfield(d, 'gordmode')
      factors.gordmode = double(d.gordmode);
    end
    factors.theomode = 1;
    [density_psd_per_hz, ~] = ISR_main(ion, d.ne, d.te, d.ti, ...
                                          fractions, f, d.radar_hz, 180, factors);
  end
  % Both implementations already return a density-scaled PSD per hertz.
  S_total = reshape(real(density_psd_per_hz), 1, []) / d.ne;
end
