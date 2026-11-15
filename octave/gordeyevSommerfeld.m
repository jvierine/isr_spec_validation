function J = gordeyevSommerfeld(theta, psin, alpha, phi, psic_para, psic_perp)
  % Use the upstream ISRTS SommerfeldIntegral and particle ACF, with tighter
  % integration controls for the near-perpendicular lower-hybrid window.
  parameters = [psin, phi, alpha, psic_para, psic_perp];
  [J, ~, ~] = SommerfeldIntegral(@SingleParticleACF, 0, 1, 64, theta, ...
                                 parameters, [1e-11, 2048, 1e-12, 131072]);
end
