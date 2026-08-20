import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = path.resolve(process.argv[2]);
const previewDir = path.join(outputDir, "business-workbook-previews");
await fs.mkdir(previewDir, { recursive: true });

function parseCsv(text) {
  const rows=[]; let row=[], cell="", quoted=false;
  for(let i=0;i<text.length;i++){const c=text[i]; if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"')quoted=false;else cell+=c;}else if(c==='"')quoted=true;else if(c===','){row.push(cell);cell="";}else if(c==='\n'){row.push(cell.replace(/\r$/, ""));rows.push(row);row=[];cell="";}else cell+=c;}
  if(cell||row.length){row.push(cell);rows.push(row);} if(rows[0]?.[0]?.charCodeAt(0)===0xFEFF)rows[0][0]=rows[0][0].slice(1); return rows.filter(r=>r.some(Boolean));
}
function col(n){let s="";for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}

const jobs = [
  ["customer_voice_library.csv","customer_voice_library.xlsx","Voice Library"],
  ["customer_voice_library.csv","cleaned_reviews.xlsx","Cleaned Reviews"],
  ["product_improvement_backlog.csv","product_improvement_backlog.xlsx","Product Backlog"],
  ["marketing_insight_playbook.csv","marketing_insight_playbook.xlsx","Marketing Playbook"],
  ["support_content_backlog.csv","support_content_backlog.xlsx","Support Backlog"],
  ["voc_action_plan.csv","voc_action_plan.xlsx","VOC Action Plan"],
];
const receipts=[];
for(const [csvName,xlsxName,sheetName] of jobs){
  const matrix=parseCsv(await fs.readFile(path.join(outputDir,csvName),"utf8")); const cols=Math.max(...matrix.map(r=>r.length)); const padded=matrix.map(r=>[...r,...Array(cols-r.length).fill("")]);
  const wb=Workbook.create(); const sheet=wb.worksheets.add(sheetName); sheet.showGridLines=false; sheet.freezePanes.freezeRows(1); sheet.getRangeByIndexes(0,0,padded.length,cols).values=padded;
  sheet.getRangeByIndexes(0,0,1,cols).format={fill:"#111827",font:{bold:true,color:"#FFFFFF"},wrapText:true}; sheet.getRangeByIndexes(0,0,padded.length,cols).format.autofitColumns();
  for(let c=0;c<cols;c++){const h=String(padded[0][c]||""); const width=/voice|review|evidence|action|root|message|metric|url|text|summary/i.test(h)?34:18; sheet.getRange(`${col(c)}:${col(c)}`).format.columnWidth=width;}
  if(padded.length>1){const table=sheet.tables.add(`A1:${col(cols-1)}${padded.length}`,true,`${sheetName.replace(/[^A-Za-z0-9]/g,"")}Table`);table.style="TableStyleMedium2";table.showFilterButton=true;}
  const headers=new Map(padded[0].map((h,i)=>[String(h),i]));
  for(const [name,values] of [["Priority",["P0","P1","P2","P3","Monitor"]],["priority",["P0","P1","P2","P3","Monitor"]],["Status",["Not Started","In Progress","Done","Blocked"]]]){if(headers.has(name)&&padded.length>1)sheet.getRange(`${col(headers.get(name))}2:${col(headers.get(name))}${padded.length}`).dataValidation={rule:{type:"list",values}};}
  const preview=await wb.render({sheetName,range:`A1:${col(Math.min(cols-1,9))}${Math.min(padded.length,25)}`,autoCrop:"all",scale:0.8,format:"png"}); await fs.writeFile(path.join(previewDir,xlsxName.replace(".xlsx",".png")),new Uint8Array(await preview.arrayBuffer()));
  const errors=await wb.inspect({kind:"match",searchTerm:"#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",options:{useRegex:true,maxResults:100},summary:"formula errors"});
  const exported=await SpreadsheetFile.exportXlsx(wb); const out=path.join(outputDir,xlsxName); await exported.save(out); receipts.push({output:out,rows:padded.length-1,formulaErrors:errors.ndjson||""});
}
await fs.writeFile(path.join(previewDir,"verification.json"),JSON.stringify(receipts,null,2)); console.log(JSON.stringify(receipts));
