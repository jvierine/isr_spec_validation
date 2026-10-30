# Run the pinned Buchert source in Julia; identity is stored in HDF5 metadata.
using HDF5, SHA
include(joinpath(@__DIR__, ".cache", "IncoherentScatter.jl", "src", "IncoherentScatter.jl"))
using .IncoherentScatter
root=@__DIR__
input=length(ARGS)>0 ? ARGS[1] : joinpath(root,".cache/additional_inputs.h5")
output=length(ARGS)>1 ? ARGS[2] : joinpath(root,".cache/additional_julia.h5")
folder=joinpath(root,".cache/IncoherentScatter.jl")
entry=joinpath(folder,"src/IncoherentScatter.jl")
h5open(input,"r") do src
    h5open(output,"w") do dst
        for name in keys(src["cases"])
            q=src["cases/"*name]; a=attributes(q)
            out=create_group(dst,name*"/Buchert")
            at=attributes(out)
            at["git_commit"]=strip(read(`git -C $folder rev-parse HEAD`,String))
            at["code_sha256"]=bytes2hex(sha256(read(entry)))
            at["adapter_sha256"]=bytes2hex(sha256(read(@__FILE__)))
            at["julia_version"]=string(VERSION)
            if read(a["nu_en_s_1"])!=0
                at["status"]="unsupported"
                at["reason"]="This interface has no electron-neutral BGK input."
                continue
            end
            try
                ne=Float64(read(a["ne_m3"])); te=Float64(read(a["te_K"])); ti=Float64(read(a["ti_K"]))
                B=Float64(read(a["B_T"])); angle=Float64(read(a["angle_k_B_deg"]))
                f=vec(read(q["frequency_hz"])); masses=vec(read(q["ion_masses_u"])); fractions=vec(read(q["ion_fractions"]))
                s=ScatterVolume(tfeff=Float64(read(a["f_r_MHz"]))*1e6,system=1/pi,b=B,alpha=deg2rad(angle))
                # Resolve the constructor's 0/0 at B=0, alpha=0 by its parallel
                # Maxwellian limit. The source's spectral equations are unchanged.
                if B==0; s.sinfac=0.; s.cosal=1.; end
                ions=ntuple(i->Ion(i<=length(masses) ? masses[i] : 1.),3)
                frac=ntuple(i->i+1<=length(fractions) ? fractions[i+1] : 0.,2)
                plasma=Plasma(ne,te,ti,s,length(masses),ions,frac)
                # Native vector routine recognizes DC only at index 1.
                values=[(x==0 ? pwrspec(plasma,s) : pwrspec(x,plasma,s))/ne for x in f]
                all(isfinite,values) || error("Nonfinite spectrum")
                out["S_total"]=values
                at["status"]="computed"
                println(name," Buchert computed")
            catch err
                at["status"]="error"; at["reason"]=sprint(showerror,err)
                println(name," Buchert ",sprint(showerror,err))
            end
        end
    end
end
