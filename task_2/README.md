# Task 2 — S3 static flood dashboard

Static site for Amazon S3. Upload these four files to the bucket root:

```
your-bucket/
├── index.html
├── style.css
├── script.js
└── flood_data_filtered.csv
```

`flood_data_filtered.csv` is the Nepal district table from Task 1 (`filtered_district_deaths.csv`) plus map coordinates. The page fetches that CSV in the browser and draws filters, charts, a map, and a table.

## Local check

S3 and browsers block `file://` fetches. From this folder:

```powershell
python -m http.server 8080
```

Open http://localhost:8080

## S3 deploy

1. Create a bucket (example name `nepal-flood-2026`).
2. Turn on **Static website hosting** → index document `index.html`.
3. Add a public-read bucket policy for `s3:GetObject` on `arn:aws:s3:::nepal-flood-2026/*` if the site should be public.
4. Upload the four files to the bucket root (no extra folders).

AWS CLI:

```powershell
aws s3 sync . s3://your-bucket-name --exclude "*" --include "index.html" --include "style.css" --include "script.js" --include "flood_data_filtered.csv"
```

Website URL shape: `http://your-bucket-name.s3-website-<region>.amazonaws.com`
