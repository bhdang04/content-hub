"""Step 3: engagement, views, follower growth from TikTok Studio zips in data/raw/.
Run: python3 src/analyze.py
Watch time: not in these exports, so not computed."""
from data import videos, overview, fol, viewers, act

# --- per video engagement ---
v = videos.copy()
v["eng_rate_%"] = (v[["Total likes", "Total comments", "Total shares"]].sum(axis=1)
                   / v["Total views"].where(v["Total views"] > 0) * 100).round(2)
v["title"] = v["Video title"].astype(str).str[:40]
print("== Videos (by views) ==")
print(v.sort_values("Total views", ascending=False)[
    ["title", "Post time", "Total views", "Total likes", "Total comments", "Total shares", "eng_rate_%"]
].to_string(index=False))
print("\nMedian engagement rate %:", v["eng_rate_%"].median(),
      "| mean views:", round(v["Total views"].mean(), 1),
      "| median views:", v["Total views"].median())

# --- daily views / engagement, weekly trend ---
o = overview.set_index("Date")
o["eng"] = o[["Likes", "Comments", "Shares"]].sum(axis=1)
w = o.resample("W")[["Video Views", "Profile Views", "eng"]].sum()
w["eng_rate_%"] = (w["eng"] / w["Video Views"].where(w["Video Views"] > 0) * 100).round(2)
print("\n== Last 12 weeks ==")
print(w.tail(12).to_string())
print("\nTotals (all period):", o[["Video Views", "Profile Views", "Likes", "Comments", "Shares"]].sum().to_dict())
print("Best 5 days by views:\n", o["Video Views"].nlargest(5).to_string())

# --- follower growth ---
f = fol.set_index("Date")
diff = f["Followers"].diff().fillna(0)
print("\n== Followers ==")
print("Start:", f["Followers"].iloc[0], "End:", f["Followers"].iloc[-1],
      "Net:", f["Followers"].iloc[-1] - f["Followers"].iloc[0])
print("Last 30d net:", diff.tail(30).sum(), "| prior 30d net:", diff.iloc[-60:-30].sum())
print("Best 5 days:\n", diff.nlargest(5).to_string())
m = diff.resample("ME").sum()
print("Monthly net:\n", m.tail(6).to_string())
print("Followers at the end of each week (last 12):\n", f["Followers"].resample("W").last().tail(12).astype(int).to_string())

# --- viewers: new vs returning ---
vw = viewers.set_index("Date")
new, ret = vw["New Viewers"].sum(), vw["Returning Viewers"].sum()
print("\n== Viewers (all period) ==")
print(f"New: {new:,.0f} | Returning: {ret:,.0f} | New share %: {new / (new + ret) * 100:.1f}")

# --- when followers are active ---
top = act.groupby("Hour")["Active followers"].mean().nlargest(3)
print("\nTop 3 hours by avg active followers:\n", top.round(0).to_string())
