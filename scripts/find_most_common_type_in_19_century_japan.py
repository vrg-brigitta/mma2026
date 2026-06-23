import pandas as pd

df = pd.read_csv("dataset/data/augmented_dataset.csv")
df.columns = [c.strip() for c in df.columns]

jp = df[df["culture"].astype(str).str.contains("Japan|Japanese", case=False, na=False)]

# # Print all periods
# for p in sorted(jp["period"].dropna().unique(), key=str):
#     print(p)

# I don't know who labeled it but this is sad.
# Manual selection with significant overlap with 19th century.
SELECTED_PERIODS = [
    "Edo (1615–1868)",
    "Edo (1615–1868) or Meiji (1868–1912)",
    "Edo (1615–1868) or Meiji (1868–1912) period",
    "Edo (1615–1868) or Meiji period (1868–1912)",
    "Edo (1615–1868)–Meiji (1868–1912) period",
    "Edo (1615–1868)–Meiji period (1868–1912)",
    "Edo (1615–1868)–Meji period (1868–1912",
    "Edo (1615–1868)–Shôwa period (1926–89)",
    "Edo (period 1615–1868)",
    "Edo perid (1615–1868)",
    "Edo period  (1615–1868)",
    "Edo period (1615-1868)",
    "Edo period (1615–1867",
    "Edo period (1615–1868",
    "Edo period (1615–1868)",
    "Edo period (1615–1868)",
    "Edo period (1615–1868) ?",
    "Edo period (1615–1868) or Meiji period (1868–1912)",
    "Edo period (1615–1868), Kanei era (1624–43)",
    "Edo period (1615–1868), Kyōhō (1716–36)",
    "Edo period (1615–1868)Vertical ōban;",
    "Edo period (1615–1868)d",
    "Edo period (1615–1868)–Meiji period (1868–1912)",
    "Edo period (1615–1868)–early Bunka period (1804–18)",
    "Edo period (1644–1911)",
    "Edo period(1615–1868)",
    "Golden Age of Ukiyo-e (1780 to 1804)",
    "Late Edo (1615–1868) or Meiji (1868–1912) period",
    "Late Edo (1615–1868) or early Meiji (1868–1912) period",
    "Meiji  period (1868–1912)",
    "Meiji Period (1868 to 1912)",
    "Meiji period (1868-1912)",
    "Meiji period (1868–1912",
    "Meiji period (1868–1912)",
    "Meiji period (1869–1912)",
    "Popularization of Woodblock Printing (1804 to 1868)",
    "early Meiji period (1868–1912)",
    "late Edo (1615–1868) or Meiji (1868–1912) period",
    "late Edo (1615–1868) or early Meiji (1868–1912) period",
    "late Edo (1615–1868)-early Meiji period (1868–1912)",
    "late Edo (1615–1868)–early Meiji (1867-1912) period",
    "late Edo (1615–1868)–early Meiji (1868–1912) period",
    "late Edo Period",
    "late Edo period (1615–1868)",
    "late Edo period (1615–1868)–early Meiji period (1868–1912) ?"
]

oracle_set = jp[jp["period"].isin(SELECTED_PERIODS)]
oracle_total = len(oracle_set)
type_counts = oracle_set["type"].value_counts(dropna=True)

print(oracle_total)
print(type_counts.to_string())