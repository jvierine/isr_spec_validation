# Native Julia Buchert timing. Run with taskset -c 0, JULIA_NUM_THREADS=1.
using HDF5, Statistics
include(joinpath(@__DIR__, ".cache", "IncoherentScatter.jl", "src", "IncoherentScatter.jl"))
using .IncoherentScatter

root = @__DIR__
f, reference = h5open(joinpath(root,"tables/expanded/f_region_440.2MHz.h5"),"r") do h
    (vec(read(h["frequency_hz"])), vec(read(h["Buchert/S_total"])))
end
s = ScatterVolume(tfeff=440.2e6,system=1/pi,b=0.,alpha=0.)
s.sinfac=0.; s.cosal=1.
ions=(Ion(16.),Ion(1.),Ion(1.))
p=Plasma(1e11,2000.,1000.,s,1,ions,(0.,0.))
run() = [(x==0 ? pwrspec(p,s) : pwrspec(x,p,s))/1e11 for x in f]

result=run() # warm up compilation and the kernel
err=maximum(abs.(result-reference))/max(maximum(abs.(result)),maximum(abs.(reference)))
@assert isfinite(err) && err <= 1e-6
elapsed=Float64[]
for _ in 1:7
    start=time_ns()
    value=run()
    push!(elapsed,(time_ns()-start)*1e-9)
    @assert maximum(abs.(value-result))/maximum(abs.(result)) <= 1e-9
end
@assert all(isfinite,elapsed) && all(>(0),elapsed)
h5open(joinpath(root,"tables/speed_buchert.h5"),"w") do h
    h["Buchert/elapsed_s"]=elapsed
    a=attributes(h["Buchert"])
    a["median_elapsed_s"]=median(elapsed)
    a["min_elapsed_s"]=minimum(elapsed)
    a["max_elapsed_s"]=maximum(elapsed)
    a["error_vs_saved"]=err
    attributes(h)["host"]="avaruus"
    attributes(h)["threads_per_call"]=1
    attributes(h)["cpu_affinity"]="0"
    attributes(h)["julia_version"]=string(VERSION)
    attributes(h)["timing_scope"]="full spectrum function; 1 warm-up; 7 timed calls; no startup or HDF5 I/O"
end
println("Buchert ",median(elapsed)," ",err)
