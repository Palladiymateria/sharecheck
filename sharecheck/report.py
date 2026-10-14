from html import escape


def html_report(result):
    rows = []
    for f in result["findings"]:
        location = f["path"] + (f':{f["line"]}' if f["line"] else "")
        rows.append(f'<article class="{f["severity"]}"><span>{escape(f["severity"].upper())}</span><h2>{escape(f["title"])}</h2><code>{escape(location)}</code><p>{escape(f["advice"])}</p></article>')
    count = len(result["findings"])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShareCheck report</title><style>
    *{box-sizing:border-box}body{margin:0;background:#101820;color:#edf3f7;font:16px/1.6 system-ui,sans-serif}main{max-width:920px;margin:60px auto;padding:0 24px}header{border-bottom:1px solid #344452;padding-bottom:30px}.brand{color:#72e2b4;letter-spacing:.15em;font-weight:700}h1{font-size:clamp(32px,6vw,58px);line-height:1.1;margin:22px 0}h2{font-size:20px;margin:8px 0}p{color:#bac9d5}code{overflow-wrap:anywhere;color:#b9d4ed}article{background:#192630;border:1px solid #344452;border-left:4px solid #7fa5cd;border-radius:10px;margin:16px 0;padding:22px}article.error{border-left-color:#ff8b8b}article.warning{border-left-color:#f0c575}span{font-size:11px;letter-spacing:.15em}footer{margin:32px 0;color:#bac9d5}@media print{body{background:white;color:black}article{background:white;break-inside:avoid}p,code,footer{color:#333}}
    </style><main><header><div class="brand">SHARECHECK / LOCAL REPORT</div><h1>Inspect before you publish.</h1><code>''' + escape(result["root"]) + f'</code><p>{result["stats"]["files"]} files inventoried · {result["stats"]["text_files"]} text files checked · {count} findings</p></header>' + ("".join(rows) or "<article><h2>No findings in checked files.</h2><p>Review the coverage limits below before publishing.</p></article>") + f'<footer>Skipped content: {result["stats"]["skipped_content"]} files. Skipped file symlinks: {result["stats"]["skipped_links"]}. Dependency folders and .git are excluded. Only UTF-8 text up to 2 MiB is inspected. Git history and arbitrary passwords are not checked. No file contents or matched secrets appear in this report. Paths may still be private.</footer></main></html>'
