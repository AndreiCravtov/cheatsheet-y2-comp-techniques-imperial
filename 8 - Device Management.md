# Principles of I/O Hardware
## I/O Devices: Block, Character, Other
I/O devices can be roughly divided into two categories: ***block devices*** and ***character devices***:
- ***Block devices***: store data in <u>fixed-size blocks</u>, each block one with <u>its own address</u>
	- Transfers in units of *one or more* entire (consecutive) blocks
	- Possible to read/write each block <u>independently</u> of the other blocks
	- e.g. HDDs, SSDs, magnetic tape drives, etc.
- ***Character devices***: delivers/accepts a <u>stream of characters</u>, disregarding any block structure
	- <u>Not addressable</u> and has <u>no seek operation</u>
	- e.g. printers, network interfaces, mice, etc.

This classification scheme is not perfect. Some devices do not fit in:
- ***Clocks***: 
	- not <u>block addressable</u> & don't generate/accept <u>character streams</u>
	- They just <u>cause interrupts</u> at well-defined intervals
- ***Memory-mapped screens***: don't fit into this model
- ***Touch screens:*** don't fit into this model

## Device Controllers/Adapters
<u>I/O units</u> often consist of a <u>mechanical component</u> and an <u>electronic component</u>. The electronic component is called the ***device controller*** or ***adapter***.
- On PCs it is often a <u>chip on the motherboard</u> or a [PCB](https://en.wikipedia.org/wiki/Printed_circuit_board) which can be inserted into a (PCIe) expansion slot
- <u>Controller</u> usually has a <u>connector</u> on it, into which a cable leading to the <u>device</u> itself can be plugged
- Many <u>controllers</u> can handle multiple devices
- If the <u>interface</u> between the <u>controller</u> & <u>device</u> is standard, companies make controllers/devices that fit that interface
	- e.g. SATA, SCSI, USB, etc.

Each <u>controller</u> has a few <u>registers</u> that are used for communicating with the <u>CPU</u>:
- <u>Writing</u> into these registers: <u>commands</u> the device to deliver data/accept data/switch itself on or off/etc.
- <u>Reading</u> from these registers: <u>learn</u> what the device’s state is, e.g. is is prepared to accept a new command, etc

Many ***devices*** have a <u>data buffer</u> that can be read+written to:
- e.g. a common way for computers to <u>display pixels</u> on the screen is <u>video RAM</u>
	- a data buffer for <u>programs/OS</u> to write into

## Memory-Mapped & Port-Mapped I/O
The ***Port-Mapped I/O*** approach assigns an ***I/O port*** number to [[#Device Controllers/Adapters|control registers and buffers]]:
- Set of all the ***I/O ports*** form the <u>I/O port space</u>
- Access to ***I/O ports*** is protected
	- ordinary user programs cannot access it
	- only the operating system can
- Access is done with special <u>I/O instructions</u>, e.g. `IN REG,PORT` and `OUT PORT,REG`
- Most early computers worked this way

The ***Memory-Mapped I/O*** approach maps all [[#Device Controllers/Adapters|control registers and buffers]] to the <u>memory address space</u>:
- Commonly at/near the top of the <u>address space</u>
- ***Pros***: 
	- no need for special ASM instructions, so [[#Device Drivers|device drivers]] can be written entirely in C/C++
	- no special protection to <u>memory-mapped</u> addresses, so the OS can be flexible with how it delegates device access
		- e.g. omit <u>memory-mapped</u> addresses from [[7 - Memory Management#Virtual Memory|user's virtual address space]]
		- e.g. give <u>some users</u> control over specific devices but <u>not others</u>, allowing [[#Device Drivers|device drivers]] to run in <u>User Mode</u>
			- prevents a <u>driver crash</u> from taking down the entire system
	- <u>reuse</u> the same ASM <u>instructions</u> as those used on <u>normal memory</u>
		- one instruction can do two things, e.g. instead of <u>first</u> reading an ***I/O port*** <u>then</u> doing something with it, you can <u>just do</u> that thing <u>in one go</u>
		- this <u>reduces the number of instructions</u> needed to be executed, therefore <u>more efficient</u>
- ***Cons***:
	- Modern computers often [[7 - Memory Management|cache memory]] but caching <u>memory-mapped</u> addresses is ***DISASTEROUS***
		- both hardware & OS have to be designed to <u>selectively disable caching</u> which can be very complex
	- Modern systems also have multiple buses (memory, PCIe, SCSI, and USB)
		- I/O devices have no way of seeing memory addresses as they go by on the memory bus
		- Additional hardware/software complexity is needed to resolve this issue
			- e.g. CPU uses non-memory buses as fallback if memory bus fails to respond
			- e.g. put a snooping device on memory bus & pass all addresses presented to potentially interested I/O devices
			- e.g. preload address-ranges to memory-controller chip at boot time & it will redirect addresses to the appropriate bus thereafter

![[Pasted image 20250106163712.png|500]]

## Direct Memory Access (DMA)
The <u>CPU</u> can requesting data from an [[#Device Controllers/Adapters|I/O controller]] <u>one byte at a time</u> wastes its time, so ***DMA (Direct Memory Access)*** is often used:
- Can only use ***DMA*** if hardware has a <u>DMA controller</u>, most systems do
- Most commonly its a single <u>DMA controller</u> (e.g. on the motherboard) 
	- for regulating transfers to <u>multiple devices</u>, 
	- often <u>concurrently</u>
- <u>DMA controller</u> has <u>access to system bus</u> <u>independent of the CPU</u>
- Contains several <u>registers</u> that can be <u>written/read by CPU</u>
	- e.g. memory address register, byte count register, control registers, etc.
	- these specify the I/O port to use, direction of transfer, transfer unit, number of bytes to transfer in <u>one burst</u>, etc.

<u>The CPU programs the DMA controller</u> and lets it <u>run parallel to the CPUs execution</u>:
- The <u>DMA controller</u> instructs the [[#Device Controllers/Adapters|device I/O controllers]] to perform the appropriate operations
- When <u>one unit of work</u> is done, the [[#Device Controllers/Adapters|device I/O controller]] sends an <u>acknowledgment signal</u> to the <u>DMA controller</u>
- For each <u>acknowledgment signal</u>, the <u>DMA controller</u> decrements a <u>counter</u> which keeps track of progress
- When the <u>counter</u> reaches 0, the workload is complete and the <u>DMA controller</u> sends an appropriate [[1.1 - Interrupts|interrupt]] to the CPU

The above are simple cases of <u>DMA controllers</u>, but ones with <u>more complex capabilities</u> exist:
- Can be programmed to <u>handle multiple transfers</u> at the same time
	- multiple sets of <u>control registers</u> internally, one for each channel
	- may use <u>round-robin</u> or <u>priority queue</u> internally to decide which device to service next
	- often each [[#Device Controllers/Adapters|device controller]] being serviced gets a separate channel for <u>acknowledgment signals</u>
- Buses can often operate in two modes: <u>word-at-a-time</u> & <u>block</u> mode
	- Often, <u>DMA controllers</u> can also operate in either mode
	- In <u>word-at-a-time</u> mode: the <u>DMA controller</u> requests the transfer of <u>one word</u> and gets it
		- If the <u>CPU</u> also wants the bus, it <u>has to wait</u>
		- The mechanism is called <u>cycle stealing</u>
	- In <u>block</u> mode: <u>DMA controller</u> tells the [[#Device Controllers/Adapters|device]] to acquire the bus, issue a series of transfers, then release the bus
		- this is called ***burst mode***
		- <u>multiple words</u> can be transferred for the <u>price of one bus acquisition</u>
		- can <u>block</u> the CPU and other devices for a <u>substantial period</u> if a long burst is being transferred
- In the above model (<u>fly-by-mode</u>), the the DMA controller tells the device controller to transfer the data directly to main memory
	- some <u>DMA controllers</u> have the [[#Device Controllers/Adapters|device controller]] send the word to the <u>DMA controller</u>,
		- which then writes the word to wherever it is supposed to go
	- This scheme requires an extra bus cycle per word transferred,
		- but is more flexible in that it can also perform device-to-device copies and even memory-to-memory copies
	

## Interrupt handlers for hardware interrupts
- For [[#I/O Devices Block, Character, Other|block devices]]: on transfer completion, signal [[#Device Drivers|device handler]]
- For [[#I/O Devices Block, Character, Other|character devices]]: when character transferred, process next character
![[Pasted image 20250106190623.png|500]]
#todo rest of this chapter in 5.1.5 Interrupts Revisited, esp Precise and Imprecise Interrupts


# Principles of I/O Software
## Goals of I/O Software
***Device independence***: write programs that can access <u>any</u> I/O device without having to specify the <u>device type</u> or <u>device instance</u> in advance
- Some differences which the OS has to abstract are: 
	- Unit of data transfer: character or block
	- Supported operations: e.g. read, write, seek
	- Synchronous or asynchronous operation
	- Speed differences
	- Sharable (e.g. disks) or single user (e.g. printer, DVD-RW)
	- Types of error conditions
***Uniform naming***: name of file/device should be a string/integer not dependent on device in any way
***Error handling***: should be handled as close to the hardware as possible
- Either the controller or [[#Device Drivers|driver]] should handle the error transparently
- Only if the lower layers are not able to deal with the problem should the upper layers be told about it
***Synchronous (blocking) vs. asynchronous (interrupt-driven)***:
- Most physical I/O is <u>asynchronous</u>
- Most I/O code is easier to write <u>synchronously</u>
- The OS must make <u>interrupt-driven</u> operations <u>appear blocking</u> to the user programs
- The OS must *still* provide <u>asynchronous API</u> for use in <u>performance-critical</u> user programs
***Buffered vs. non-buffered I/O***: often data that come off a device cannot be stored directly in their final destination
- e.g. <u>packets</u> coming off a <u>network</u> cannot be directed to the right place until they have been <u>stored and inspected</u> for their <u>port number</u>
- some destination devices (e.g. digital audio devices) have limitations on data-transfer rates, so a buffer is used to "normalize" those
- Buffering involves considerable copying and often has a major impact on I/O performance
***Sharable vs. dedicated devices***: 
![[Pasted image 20250106195318.png|400]]

## Ways to do I/O
1. ***Programmed I/O***: CPU programs [[#Memory-Mapped & Port-Mapped I/O|I/O control registers]] directly and blocks until the operation is done
	- This is done via ***polling*** the [[#Device Controllers/Adapters|device]] until its done, called ***busy waiting***
	- Wastes CPU time and inefficient
2. ***Interrupt-Driven I/O***: The CPU programs [[#Memory-Mapped & Port-Mapped I/O|I/O control registers]] directly and continues doing other things
	- the [[#Device Controllers/Adapters|device]] will send an [[1.1 - Interrupts|interrupt]] to the CPU once done
	- can still be very inefficient with <u>unbuffered</u> [[#I/O Devices Block, Character, Other|character devices]] which will interrupt on every character
3. ***I/O using Direct Memory Access (DMA)***: The CPU programs [[#Direct Memory Access (DMA)|a DMA controller]] and continues doing other things
	- the <u>DMA controller</u> will perform the <u>entire</u> operation and send an [[1.1 - Interrupts|interrupt]] to the CPU once done
	- may be inefficient in certain circumstances, because [[#Direct Memory Access (DMA)|DMA controllers]] are usually <u>much</u> slower than the CPU

# I/O Software Layers
<u>I/O software</u> is typically organized in <u>four layers</u>. Each layer has a <u>well-defined function</u> to perform and a <u>well-defined interface</u> to the adjacent layers
![[Pasted image 20250106201355.png|500]]

## Interrupt-Handlers in the Software Layers
[[#Interrupt handlers for hardware interrupts|Interrupt handlers]] should aim to be as <u>buried</u> as possible, doing as <u>little</u> as possible.
- e.g. have a [[#Device Drivers|driver]] start an I/O operation and <u>block</u> (like by [[5 - Synchronization#Semaphores|downing a semaphore]]) and the <u>interrupt-handler</u> only <u>unblocks</u> it (like by <u>upping that semaphore</u>)
- e.g. for others its a [[5 - Synchronization#Monitor Locks (monitors) on Condition Variables (condvars)|condvar signal]] or other kind of message etc. which will make the device driver resume
- the above works best if the <u>driver</u> is structured as a [[2 - Processes|process]]
#todo the rest of 5.3.1 Interrupt Handlers in textbook

## Device Drivers
![[Pasted image 20250106202425.png|400]]
Device drivers are normally positioned below the rest of the operating system
![[Pasted image 20250106202559.png|500]]
Most operating systems define a <u>standard interface</u> that all [[#I/O Devices Block, Character, Other|block]] drivers must support and a <u>second standard interface</u> that all [[#I/O Devices Block, Character, Other|character]] drivers must support.
#todo 5.3.2 Device Drivers in textbook

## Device-Independent I/O software
The basic function of the ***device-independent software*** is to perform the I/O functions that are <u>common</u> to <u>all devices</u> and to provide a <u>uniform interface</u> to the <u>user-level software</u>
![[Pasted image 20250106203452.png|400]]

### Uniform Interfacing for Device Drivers
A major issue in an OS is how to make all I/O devices and drivers look more or less the same. If they weren't the same, we would have to hack on the OS for each new device
![[Pasted image 20250106203726.png|600]]
Not all devices are <u>absolutely identical</u>, but there are only a <u>small number of device types</u> which need to be accounted for
- e.g. classes of device like disks, printers, network stream
- OS defines a set of functions that the driver of a specific device type must supply
The device-independent software takes care of mapping symbolic device names onto the proper driver:
- e.g. for UNIX a device name, such as /dev/disk0,  uniquely specifies the i-node for a special file
	- this i-node contains the major device number, which is used to locate the appropriate driver
	- The i-node also contains the minor device number, which is passed as a parameter to the driver in order to specify the unit to be read or written

### Buffering
![[Pasted image 20250106204627.png|400]]
#todo this entire section in the OS book (ykwim)

### Error Reporting
- Programming errors
- actual I/O errors
- #todo more detail

### Allocating and Releasing Dedicated Devices
Some devices, such as printers, can be used only by a single process at any given moment. The OS has to allocate access to this device, and release access to it too.
#todo 

### Device-Independent Block Size
Different SSDs have different flash page sizes, while different disks may have different sector sizes.
It is up to the device-independent software to hide this fact and provide a uniform block size to higher layers

## User-Space I/O Software
### User-Space I/O Libraries
Most user-space I/O code is library code which simply arranges arguments in the right way for a SYSCALL,
- sometimes more complex logic is done i.e. `printf` and `scanf` in C

### Spooling Daemons
![[Pasted image 20250106205848.png|400]]
#todo add more detail from textbook
#todo add more detail from slides specifically abt linux (this is omitted from books) this is <font color="#ff0000">VERYYYYYYY important</font>, critical info is in there missing from here
