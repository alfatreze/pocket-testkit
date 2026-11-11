# Host side of pk_vjtag_regwin, run with Quartus' quartus_stp (not system-console):
#   quartus_stp -t host/pk_vjtag.tcl id
#   quartus_stp -t host/pk_vjtag.tcl r 0x0
#   quartus_stp -t host/pk_vjtag.tcl w 0x1 0xCAFE1234
#   quartus_stp -t host/pk_vjtag.tcl batch cmds.txt     (lines: "r ADDR" | "w ADDR DATA" | "id")
# Output lines: "r ADDR DATA ERR" / "w ADDR DATA ERR" / "id VALUE". ADDR is a 15-bit word address.
# Starting quartus_stp takes seconds; use batch for many accesses. Not run on hardware by this
# kit: the DR bit order (LSB first) and capture timing are the things to confirm first, with
# "id" (expects 0x504B0101) and the demo registers (0x0 = 0xD0C0FFEE, 0x1 = scratch).
set instance 0

proc pk_open {} {
    set hw [lindex [get_hardware_names] 0]
    set dev [lindex [get_device_names -hardware_name $hw] 0]
    open_device -hardware_name $hw -device_name $dev
    device_lock -timeout 10000
}
proc pk_close {} { catch {device_unlock}; catch {close_device} }
proc pk_ir {v} {
    global instance
    device_virtual_ir_shift -instance_index $instance -ir_value $v -no_captured_ir_value
}
proc pk_dr {len hexval} {
    global instance
    return [device_virtual_dr_shift -instance_index $instance -length $len -dr_value $hexval -value_in_hex]
}
proc pk_id {} { pk_ir 3; return [pk_dr 32 00000000] }
proc pk_xfer {we addr data} {
    set frame [expr {($we << 47) | (($addr & 0x7FFF) << 32) | ($data & 0xFFFFFFFF)}]
    pk_ir 1
    pk_dr 48 [format %012X $frame]
    for {set i 0} {$i < 200} {incr i} {
        pk_ir 2
        set rsp [expr 0x[pk_dr 35 0000000000]]
        if {!(($rsp >> 33) & 1)} { break }
    }
    return [list [expr {$rsp & 0xFFFFFFFF}] [expr {($rsp >> 32) & 1}] [expr {($rsp >> 34) & 1}]]
}
proc pk_cmd {words} {
    set op [lindex $words 0]
    if {$op eq "id"} { puts "id 0x[pk_id]"; return }
    set addr [expr [lindex $words 1]]
    if {$op eq "w"} { set data [expr [lindex $words 2]] } else { set data 0 }
    lassign [pk_xfer [expr {$op eq "w"}] $addr $data] val err over
    puts [format "%s 0x%04X 0x%08X err=%d overrun=%d" $op $addr $val $err $over]
}

pk_open
if {[lindex $quartus(args) 0] eq "batch"} {
    set f [open [lindex $quartus(args) 1]]
    while {[gets $f line] >= 0} { if {[string trim $line] ne ""} { pk_cmd $line } }
    close $f
} else {
    pk_cmd $quartus(args)
}
pk_close
