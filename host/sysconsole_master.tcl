# JTAG-to-Avalon master path (Platform Designer "JTAG to Avalon Master Bridge"), run in
# System Console:   system-console --script=host/sysconsole_master.tcl
# (system-console lives in <quartus>/sopc_builder/bin, KB-057.) Word addresses are byte
# addresses here: word N is at 4*N when pk_avmm_master_to_bus ADDR_SHIFT is 2.
# Use master_read_memory / master_write_memory for blocks; the *_32 calls move one word per
# round trip and are slow (community reports about 3 ms per access).
set path [lindex [get_service_paths master] 0]
open_service master $path
puts [format "demo id    : 0x%08X" [master_read_32 $path 0x0 1]]
master_write_32 $path 0x4 0xCAFE1234
puts [format "scratch    : 0x%08X" [master_read_32 $path 0x4 1]]
close_service master $path
