***Memory*** is a key component of the computer :- in the<u> "von Neumann architecture"</u> model all data/code share the same memory.
***Overview:***
- [[#Basic Concepts|Basic concepts]]
	- [[#Memory Allocation|Memory allocation]]
	- [[#Swapping|Swapping]]
- [[#Virtual Memory|Virtual memory]]
	- [[#Paging|Paging]]
- [[#Demand Paging|Demand paging]]
	- [[#Page replacement algorithms|Page replacement algorithms]]
	- [[#Working set model|Working set model]]
- [[#Case Study Linux Memory Management|Linux memory management]]
***Memory management*** needs to provide:
- [[#Memory Allocation|Memory allocation]]
- <u>Memory protection</u>
- No knowledge of *how* memory is generated should be required *(e.g. instruction counter, indexing, indirection...)*
- No knowledge of what the memory address holds *(memory vs. data)* should be required
The computer has <u>CPU registers</u> and <u>main memory</u>:
![[Pasted image 20241119212829.png|400]]
- <u>Register</u> access = one cycle
- <u>Main memory</u> = many cycles
- <u>L1, L2, L3 cache</u> is between <u>register</u> and <u>main memory</u>
![[Pasted image 20241119213521.png|450]]![[Pasted image 20241119213547.png|450]]![[Pasted image 20241119213613.png|450]]


# Basic Concepts
## Memory Allocation
<u>Main memory</u> usually split into two partitions:
- Resident [[year_2_unconnected/operating systems/1 - Introduction#OS Kernel Design|operating system (kernel)]] :- Usually held in low memory with [[1.1 - Interrupts|interrupt vector]] 
- [[2 - Processes|User processes (user)]] :- Held in high memory

### Contiguous Memory Allocation
***Contiguous allocation*** with <u>relocation registers</u>:
- **<u>Base register</u>** contains value of smallest physical address
- <u>Limit register</u> contains range of logical addresses
	- Each logical address must be less than <u>limit register</u>
- <u>Memory Management Unit (MMU)</u> maps logical address dynamically
![[Pasted image 20241120233720.png|300]]
^<u>Base</u> and <u>limit registers</u> define <u>logical address space</u>

#### Memory Protection in Contiguous Memory Allocation
Check memory access valid to protect [[2 - Processes|user processes]]
- from each other
- from changing [[year_2_unconnected/operating systems/1 - Introduction#OS Kernel Design|operating-system]] code and data
![[Pasted image 20241120234121.png|400]]

### Multiple-Partition Allocation
![[Pasted image 20241120234217.png|500]]![[Pasted image 20241120234301.png|500]]

### Fragmentation
![[Pasted image 20241120234354.png|500]]
## Swapping
![[Pasted image 20241120234424.png|500]]

# Virtual Memory
![[Pasted image 20241120234652.png|600]]![[Pasted image 20241120234731.png|500]]

## Paging
![[Pasted image 20241120234802.png|500]]![[Pasted image 20241120234958.png|400]]![[Pasted image 20241121002233.png|400]]

How does page size affect things?
- <u>Smaller</u> pages => less [[#Fragmentation|internal fragmentation]] and hence more efficient memory use
- <u>Larger</u> pages => smaller memory map, less overhead for address translation, hence faster memory access

When performing [[2 - Processes#Context Switches|context switches]], the OS must
- locate the <u>page table</u> for the process that is to start running
- set the [[#Contiguous Memory Allocation|base register]] in the <u>MMU</u> so that it point to the page table in memory
- clear any now-invalid cached address translations from the [[#Translation Look-aside Buffers (TLBs)|TLB]]

### Address Translation with <u>One-Level Paging</u>
![[Pasted image 20241121001555.png|500]]![[Pasted image 20241121001607.png|500]]
***NOTE:*** careful with the ***bits*** vs. ***bytes*** units,
- its $\displaystyle 2^m$ ***bits*** of <u>address space</u>, where each <u>address</u> refers to a ***byte*** in memory
- and its $2^n$ ***bytes*** of ***page size***, which spans $2^n$ ***bits*** of <u>address space</u>
 
### Memory Protection with <u>One-Level Paging</u>
![[Pasted image 20241121002445.png|400]]![[Pasted image 20241121002517.png|400]]

## Page Table Implementations
So far we've seen basic ***One-Level Page Tables*** with <u>no caching</u>, which are kept in memory with
- ***Page-table base register (PTBR)*** points to <u>page table</u>
- ***Page-table length register (PTLR)*** indicates size
But this is <u>inefficient</u>,
- Every data/instruction access requires two memory accesses, 1) for <u>page table</u> 2) for data/instruction
	- We can use [[#Translation Look-aside Buffers (TLBs)|associative memory/TLBs]] for this
- On 64-bit machines with 4 kB page sizes [[#Address Translation with <u>One-Level Paging</u>|thats $\displaystyle p=52$ and $\displaystyle d=10$]]
	- The<u> page table</u> needs $\displaystyle 2^{p}=2^{52}$ entries
	- With 8 bytes per entry *(8 bytes is the size of an address/pointer)* thats **~30 MILLION GB....**
	- Instead of storing an entry per page, we store per frame :- e.g. [[#Page Table Type Hashed Page Table|hashed page tables]], [[#Page Table Type Inverted Page Table|inverted page tables]]

### Translation Look-aside Buffers (TLBs)
We can use special <u>fast-lookup hardware cache</u> *(in the CPU)* called ***associative memory*** to store portions of the <u>page table</u>
![[Pasted image 20241121014235.png|400]]
This associative memory, when used for the purpose of caching page tables, is called ***Translation Look-aside Buffers (TLBs)***. 
- Some ***TLBs*** store <u>address-space ids (ASIDs)</u> in entries
	- Uniquely identifies each process to provide address-space protection for that process
- ***TLBs*** usually needs to be <u>flushed</u> after [[2 - Processes#Context Switches|context switch]]
	- Can lead to substantial overhead
	- <font color="#ff0000">What about kernel pages for system calls?</font>
![[Pasted image 20241121014705.png|400]]

#### Performance: Effective Access Time
![[Pasted image 20241121014814.png|400]]
^this formula is for [[#Address Translation with <u>One-Level Paging</u>|one-level tables]] where <u>memory cycle time</u> $M$ is $M=1 \mu sec$, but we can generalize to to [[#Page Table Type Hierarchical Page Table|$n$-level tables]]
- $EAT = \displaystyle (\varepsilon + M) \cdot \alpha + (\varepsilon + M + nM) \cdot (1-\alpha) = \varepsilon + M\cdot \left[1 + \textcolor{red}{n}\cdot(1-\alpha) \right]$
	- so the cost would be $1$ [[#Translation Look-aside Buffers (TLBs)|TLB lookup]] and $1$ <u>memory lookup</u> *always happens*, and $n$ *additional* <u>memory lookups</u> if there is a <u>cache miss</u> 
- So with [[#Address Translation with <u>One-Level Paging</u>|one-level tables]] $n=1$ and $M=1$, we get $EAT = 2 + \varepsilon - \alpha$ which <u>recreated the formula from above</u>
- And for e.g. $n=4$ and $M=1$ we get $EAT = 5 + \varepsilon - 4\alpha$, etc.

### Page Table Type: Hierarchical Page Table
Break up <u>logical address space</u> into <u>multiple page tables</u>

#### Two-Level Page Tables
![[Pasted image 20241121015119.png|400]]![[Pasted image 20241121015142.png|450]]![[Pasted image 20241121015202.png|450]]

#### Three-Level Page Tables
![[Pasted image 20241121015246.png|400]]

### Page Table Type: Hashed Page Table
![[Pasted image 20241121015455.png|450]]

### Page Table Type: Inverted Page Table
![[Pasted image 20241121015511.png|450]]

## Shared Memory
![[Pasted image 20241121043002.png|450]]![[Pasted image 20241121043052.png|450]]

## Segmentation & Hybrid Paging/Segmentation Approaches
![[Pasted image 20241121043422.png|450]]![[Pasted image 20241121043557.png|700]]

## Virtual Memory Tricks
### Copy On Write (COW)
![[Pasted image 20241121051904.png|400]]![[Pasted image 20241121051922.png|400]]![[Pasted image 20241121051959.png|400]]

### Memory-mapped Files
- Map file into virtual address space using paging
- Simplifies programming model for I/O

# Demand Paging
![[Pasted image 20241121051008.png|600]]![[Pasted image 20241121051024.png|600]]

## Page Faults
![[Pasted image 20241121051211.png|400]]![[Pasted image 20241121051229.png|500]]

## Performance of Demand Paging
![[Pasted image 20241121051359.png|350]]![[Pasted image 20241121051441.png|400]]

## Page Replacement
![[Pasted image 20241121052234.png|450]]

### Basic Page Replacement Strategy
![[Pasted image 20241121052331.png|400]]![[Pasted image 20241121052345.png|500]]

### Page replacement algorithms
![[Pasted image 20241121052422.png|450]]

#### First-In-First-Out (FIFO) Algorithm
![[Pasted image 20241121052634.png|500]]![[Pasted image 20241121052741.png|400]]![[Pasted image 20241121052754.png|400]]

#### Optimal Algorithm
![[Pasted image 20241121052828.png|450]]

#### Least Recently Used (LRU) Algorithm and its approximations: Reference bit algorithm, Second chance algorithm
![[Pasted image 20241121052855.png|450]]![[Pasted image 20241121052941.png|400]]![[Pasted image 20241121053003.png|550]]

#### Counting Algorithms: <u>LFU (least frequently used)</u> algorithm, <u>MFU (most frequently used)</u> algorithm
![[Pasted image 20241121053246.png|400]]

#### [[#Working set model|Working Set (WS)]] Clock Algorithm
![[Pasted image 20241121054055.png|400]]
![[Pasted image 20241121054205.png|600]]![[Pasted image 20241121054226.png|550]]![[Pasted image 20241121054508.png|450]]

## Locality of Reference & Thrashing
Programs tend to request <u>same</u> pages in space and time, this effect is called the ***Locality of Reference***.
Therefore for program to run efficiently:
- System must maintain program's <u>favoured</u> subset of pages in main memory
- Otherwise ***thrashing*** will occur
	- Excessive paging activity causing low processor utilisation 
	- Program repeatedly requests pages from secondary storage
![[Pasted image 20241121053818.png|400]]

## Working set model
![[Pasted image 20241121053938.png|600]]

# Case Study: Linux Memory Management
## Linux: 32-bit Virtual Memory Layout
![[Pasted image 20241121043955.png|600]]![[Pasted image 20241121044018.png|500]]

## Linux: Paging
![[Pasted image 20241121044109.png|500]]

## Linux: Page Replacement
![[Pasted image 20241121054602.png|450]]![[Pasted image 20241121054630.png|700]]

# Exploiting [[#Translation Look-aside Buffers (TLBs)|cached virtual addresses]]: Meltdown attack
![[Pasted image 20241121045915.png|450]]![[Pasted image 20241121045936.png|450]]![[Pasted image 20241121050027.png|450]]
![[Pasted image 20241121050057.png|450]]
Essentially you do it like this:
- access kernel memory
- shift down to the bit you want to reveal, and mask the rest
- now index into user memory with `4096` multiplier
	- will load either `user_mem[0*4096]` or `user_mem[1*4096]` into [[#Translation Look-aside Buffers (TLBs)|cache]]
	- depending on the value of the kernel memory bit we read
- then after the branch prediction, compare the access times of `user_mem[0*4096]` and `user_mem[1*4096]`
	- the one which was cached during the branch prediction will be significantly faster
	- therefore we have gained access to the bit in the kernel space
- we can now perform this for
	- every bit in that byte (just use a different shift value)
	- every byte in some region
	- and read out things like encryption keys and so on

