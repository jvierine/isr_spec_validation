% EISCAT GUISDAP reference spectrum and timing, using the installed source.
% The source tree stays outside this repository. The pldfvv table is loaded
% directly so GUISDAP's global site setup is not needed for this pure model.
args = argv();
if numel(args) ~= 3
  error('usage: octave -q octave/eiscat_case.m INPUT.h5 OUTPUT.h5 REPEATS');
end
input_file = args{1}; output_file = args{2}; repeats = str2double(args{3});
assert(repeats >= 1 && repeats == fix(repeats));
source = getenv('EISCAT_GUISDAP_ROOT');
assert(~isempty(source) && exist(fullfile(source,'anal','guisdap_spec.m'),'file'));
here = fileparts(mfilename('fullpath'));
addpath(here,'-begin');
addpath(fullfile(source,'anal'),'-end');
global pldfvv pldfv;
table_file=fullfile(source,'matfiles','pldfvv.mat');
assert(exist(table_file,'file'));
load(table_file,'pldfvv');
load(fullfile(source,'matfiles','pldfv.mat'),'pldfv');
q=load('-hdf5',input_file);
assert(q.B==0 && q.nu_e==0 && q.nu_i==0);
assert(numel(q.ion_masses_u)>=1 && numel(q.ion_masses_u)<=3);
assert(numel(q.ion_fractions)==numel(q.ion_masses_u));
assert(abs(sum(q.ion_fractions)-1)<1e-12);
f=reshape(q.frequency_hz,1,[]);
el=[q.ne,q.te,0,0];
io=[reshape(q.ion_fractions,[],1),q.ti*ones(numel(q.ion_masses_u),1),reshape(q.ion_masses_u,[],1),zeros(numel(q.ion_masses_u),2)];
ra=[q.radar_hz,pi];
run=@() guisdap_spec(f,el,io,ra);
S_total=run();
elapsed_s=zeros(1,repeats);
for i=1:repeats
  t0=tic(); value=run(); elapsed_s(i)=toc(t0);
  assert(all(isfinite(value(:))));
  assert(max(abs(value(:)-S_total(:)))<=1e-12*max(abs(S_total(:))));
end
frequency_hz=f;
save('-hdf5',output_file,'frequency_hz','S_total','elapsed_s');
