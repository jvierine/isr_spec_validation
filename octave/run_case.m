% Octave adapter for the pinned MATLAB ISR implementations. The upstream
% source checkouts remain unchanged. Input and output are HDF5, including
% exact frequency samples and single-call timings (process startup excluded).
args = argv();
if numel(args) ~= 4
  error('usage: octave -q octave/run_case.m CODE INPUT.h5 OUTPUT.h5 REPEATS');
end
code = args{1};
input_file = args{2};
output_file = args{3};
repeats = str2double(args{4});
assert(repeats >= 1 && repeats == fix(repeats));
here = fileparts(mfilename('fullpath'));
root = fileparts(here);
case_data = load('-hdf5', input_file);
% Older MATLAB files contain Latin-1 comments. Suppress only the parser's
% UTF-8 replacement notice; retain all numerical/runtime warnings.
warning('off', 'octave:get_input:invalid_utf8');
addpath(here, '-begin');
if strcmp(code, 'Martinez')
  assert(case_data.B == 0 && case_data.nu_e == 0 && case_data.nu_i == 0);
  addpath(fullfile(root, '.cache', 'ISR_Model', 'Model_ISR'), '-end');
elseif strcmp(code, 'Sandbem')
  addpath(fullfile(root, '.cache', 'ISRTS', 'src'), '-end');
else
  error('Unknown implementation: %s', code);
end
% One untimed warm-up resolves Octave functions and JIT caches. Every timed
% call builds its own configuration and computes the complete spectrum.
S_total = octave_kernel(code, case_data);
elapsed_s = zeros(1, repeats);
for r = 1:repeats
  t0 = tic();
  result = octave_kernel(code, case_data);
  elapsed_s(r) = toc(t0);
  assert(all(isfinite(result(:))));
  assert(numel(result) == numel(S_total));
  assert(max(abs(result(:)-S_total(:))) <= 1e-12*max(S_total(:)));
end
S_total = reshape(S_total, 1, []);
frequency_hz = reshape(case_data.frequency_hz, 1, []);
save('-hdf5', output_file, 'frequency_hz', 'S_total', 'elapsed_s');
