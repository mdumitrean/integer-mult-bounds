# Exact moment and scaled finite-gate supplement

This is source/proof planning for the T370 circuit. No moment, control,
allocation or admission experiment was executed to write it. The combined
construction and admission path is in `ADMISSION-PATH.md`.

The source is Marius-Paul Dumitrean's PR2979 at
`be191346391661f4d35fc0d1508d0a6029572576`. Its complete inherited
CREDITS/NOTICE/SOURCES and original `data/words/PINS.json` remain the
attribution here. Source acquisition SHA256 is
`e5ad48ac05e897dcc2e073d29be451cfd1493ba3077e7e2de0f9460aa11a7d71`;
CLAIM SHA256 is
`436e0d297cbdf195445d3697d496ac675e95210b79e70ce602a6a6667a4c6ce9`.

## Moment normalization and exact proposal

The complete proposed profile is five times the source's *complete local
plus idle* profile, followed by one delta
`20 H1 + 19 H3 + H48 - 25 H5`. There are3330 local calls and331520 live
data/owner families, so the moment at complex exponent`a` is

```
sum_r H[r] * (r/73)^(1-a) / 331520.
```

The cycle has zero rank mass (`20+57+48-125=0`), and the complete rank mass
remains `72*331520 + 64*3330 = 24082560`. Empty rank-zero residuals contribute
zero. Both providers retain their own exact words; equal profiles do not
replace the exact dispatch identity.

`pipeline/continuation06/moment.py` uses only the trusted exact rational
`child_cost` in `research/t74-joint-twelve-retired7/vendor/ceiling.py`, SHA256
`86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc`.
It checks signed outward intervals, full-profile normalization, both strict
root brackets on a`10^-24` grid, and candidate lower root above baseline upper
root. The old `a/(1+a)` interpretation in that source's historical prose is
not used. The proposed modern outer parameter is `K=C-10^-46-10^-70`,
conditional on supplier and outer gates. The runner must bind the audited
literal T370 profile and idle profile to the checker's complete profiles.
The module's PASS is explicitly a conditional profile-moment certificate.

## Extra children and stock

The cycle creates **15 additional nonzero idle children**. The CONT01 transfer
guard requiring a nonincreasing residual-child count is therefore inapplicable.
The source literal idle counts in `admission-owners.log.txt` total52184. The
new candidate would have `5*52184+15=260935` such children. The source dedicated
bank envelope charges149184 slots atT74; its five-copy reserve is745920.
Reusing that larger reserve requires an explicit scaled dedicated-bank
construction, but the proposed count fits it without any uncharged child.

The new namespace is332029 =331520+408+8+91+2. Helper, centre, private-buffer
and coefficient-work banks are reused only after the unchanged universal
local restoration/clear contracts. Multiplying66813 byfive is not the proposed
physical-stock model. The primitive invoice must charge all3330 calls and
every changed residual, bridge, wrapper and controller operation.

## A static prefix bound and its exact premises

The previously pinned inert blocknorm specification,
`data/continuation-01/references/blocknorm-specification.py.txt`, derives

```
G = |Sp(72,2)| = 2^(36^2) product_(j=1..36) (2^(2j)-1),
stock = G * physical,
reserve_prefix = 128 + 37 + 18 + ceil(bit_length(stock)/2) + 1 + 4.
```

Its prerequisites include the full physical namespace, local native prefix
at most128, fresh residual charts, injective family embeddings and the
separate depth18 block-energy argument. PR2979's authenticated adapter
derivation changes the private-buffer namespace to91, hence overhead509,
while retaining those conditions. Under these premises,
`physical=332029<2^19` and `G<2^2628` give `bit_length(stock)<=2647`, the L2
factor at most1324, and reserve at most1512, strictly below the charged2048.
This algebra does not independently replay the current-provider native cache;
its local-prefix premise is explicitly source-bound. The new owner chronology
and residual charts still need independent checks before invoking this bound.

## The nine finite inequalities

The trusted CONT01 `admission_v2._strict_finite_invoice` lists the nine exact
finite supplier gates. With a newly justified conservative per-vertex
primitive bound`U`, local bound`B`, streamed mass`J=G*24082560`, stock`S=G*332029`,
and unchanged compiler allowance`D=64*74^3` (74 is dimension73 plus one, not
the number of replicas), the corresponding checks are

```
B < 2^48,
L = G*U + 64 < 2^6050,
D*(L+1)*(S+1)^2 < 2^30000,
2*2^30000*S^2 + 8*J + 4*S + 4 + 32*73 < 2^100000,
N = J + 2^100000 < 2^100001,
32*73*N^2 < 2^210000,
2*N + 18 < 2^210000,
2*bit_length(S) + 9909 + 252 + 2*2048 < 20161,
2*max_child_rank^2 < 73^2.
```

The row expression is at most19551 from the stock bound above, and the
retained maximum rank48 gives `2*48^2=4608<5329`. The other gates can be
evaluated with exact integers once`U` is justified. Simply multiplying an
unavailable source invoice byfive is not that justification. A feasible
route is a conservative new envelope using unchanged source-admitted local
primitive bounds, exact3330-call multiplicities, fully charged wrappers and
bridges, the745920-child reserve, and complete controller/clear costs.
The wrapper count per local instruction and retained-overcharge term must
come from the pinned compiler/controller specification before selecting a
numerical reserve. These are stated proof obligations, not passed checks.

## Native evidence boundary

The acquired `FULL-NATIVE-RECEIPT.json`, SHA256
`6d27c89d5e3a2c7f28387e4b20c462b0dff6c9fa92aacdde715d4b29cc286d41`,
maps each unchanged source word to complete native artifact hashes. Source
WORD and native expanded FULL-WORD hashes are distinct and must be related by
that explicit map. The `RELEASE-RECEIPT.json`, SHA256
`473a5f8e048e45d7e83747077a18985ef87d58da370ca3f2fe5748a057ffdb2d`,
and `ADMISSION-RESULT.json`, SHA256
`be9652312a88fd670eb09a4303679b4e875516d02a008ce90ccbca8a92e6b2ac`,
are authenticated source assertions. Their detailed referenced native-cache
files are not thereby present or independently replayed here.

The public package contains no `PHYSICAL-INVOICE.json` with the aggregate
primitive counts used by the old CONT01 adapter. A conditional source-bound
transfer may reuse unchanged local-word/native premises explicitly, while
freshly proving the changed allocation, scaled invoice, prefix and exact
outer arithmetic. Receipt hashes alone do not close those changed gates.
If the round produces only a literal fill and exact root improvement, the
missing gates must remain pending rather than being renamed admitted kappa.
