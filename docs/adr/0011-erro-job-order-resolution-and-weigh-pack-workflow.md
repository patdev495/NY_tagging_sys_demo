# 0011. Erro Job Order Resolution and Weigh Pack Workflow

## Context

Customer Erro operators previously had to enter or scan an internal Factory P/N directly (e.g. `1LAE0091C2U005MAAS`) to select a Product before entering the weighing station. In plant operations, operators work from physical Job Order paperwork (`wadoco`, e.g. `1259487`) created in ShopFloorDW ERP (`ShopFloorDW.DBO.F4801`).

While UI customer cartons use `packing_mode="item_scan"` with pre-allocated `JobOrderCartonSlot` slots, Erro cartons use `packing_mode="weight_scale"` with JIT serial allocation under strict monotonicity constraints (SSCC Modulo 10, Base32 sequential counters, and monthly reset ranges).

## Decision

1. **Job Order as Resolver and Audit Key**: Erro packing stations will require operators to input or scan a **Job Order** (`wadoco`). The system resolves the Job Order via ShopFloorDW `F4801`, extracts the Factory P/N (`walitm`), and maps it to an Erro Product via `ProductInternalFactoryPartNumber`. The Job Order string is recorded on every printed Carton record (`cartons.job_order`).
2. **Continuous Production Run without Pre-allocated Slots**: Erro retains its continuous `weight_scale` packaging mode. It will NOT generate `JobOrderCartonSlot` records or enforce serial numbers upfront. Carton SN generation remains JIT at the exact moment of weighing.
3. **Pre-pack Confirmation Dialog**: Upon scanning a valid Job Order, the station displays a summary dialog showing Job Order, Factory P/N, ERP Customer Reference (`wadl01`), total order quantity (`wauorg`), and calculated carton count (`wauorg / packed_qty`). If `wadl01` differs from the Product's catalog name, an inspection warning is shown. Operators confirm/input required batch metadata (`po_number`, `lot_number`) and press Enter to start weighing.
4. **Strict ERP Failure Policy**: If ShopFloorDW cannot be reached or the Job Order does not exist in `F4801`, the system instructs the operator to retry after a few minutes. Manual Factory P/N fallback is not provided on the packing station.
5. **Soft Quota and Progress Tracking**: The station tracks completed cartons against the Job Order's total planned cartons (`wauorg / packed_qty`). When carton count meets or exceeds the planned quantity, a visual advisory indicator is displayed without blocking the F9 print trigger.

## Consequences

- Operators work naturally with ShopFloorDW work order numbers.
- Erro cartons possess full Job Order traceability in the database.
- Monotonic serial generation and date code integrity are preserved by avoiding slot pre-allocation.
- Operators retain flexibility to complete partial or makeup cartons without being blocked by hard quotas.
