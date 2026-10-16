# luarmor script data fetcher for luarmor
this tool fetches the script data (_bsdata and superflow_bytecode data) off luarmor scripts by url or hash
it is free,open-sourced

# INSTALLATION
```git clone https://github.com/axom0022/luarmor-data-fetcher-by-axom.git```
```cd luarmor-data-fetcher-by-axom```

# HOW-TO-USE / USAGE
```python3 luarmorfetcher.py https://api.luarmor.net/files/v4/loaders/9a74869874633cdef1929e4479b1d393.lua```
or
```python3 luarmorfetcher.py 9a74869874633cdef1929e4479b1d393``` 
= automatically saves file to directory '/snap'

to specify directory, file output :
```python3 luarmorfetcher.py https://api.luarmor.net/files/v4/loaders/9a74869874633cdef1929e4479b1d393.lua -o out/outdir/fileoutput.txt```

usage is in tool too btw.
made by axom
