#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { buildArtDirectionSpec, validateArtDirectionSpec, writeArtDirectionArtifacts } from "./art_direction_system.mjs";
import { renderArtDirectionWorkbooks } from "./workbook_renderer.mjs";

function argsOf(argv) {
  const args={};
  for(let i=0;i<argv.length;i+=1){if(argv[i]==="--spec")args.spec=argv[++i];else if(argv[i]==="--output")args.output=argv[++i];}
  return args;
}

const args=argsOf(process.argv.slice(2));
if(!args.spec||!args.output){console.error("Usage: node scripts/generate_art_direction.mjs --spec <PRODUCT_PAGE_SPEC.json> --output <output-dir>");process.exit(2);}
const specPath=path.resolve(args.spec);const outputDir=path.resolve(args.output);
const spec=JSON.parse(await fs.readFile(specPath,"utf8"));
const art=buildArtDirectionSpec(spec);
const validation=validateArtDirectionSpec(art);
if(validation.status!=="PASS"){console.error(JSON.stringify(validation,null,2));process.exit(1);}
await writeArtDirectionArtifacts(spec,art,outputDir);
const workbooks=await renderArtDirectionWorkbooks(spec,art,outputDir);
await fs.writeFile(path.join(outputDir,"qa","art-direction-validation.json"),`${JSON.stringify({validation,source_spec_sha256:spec.meta.spec_sha256,workbooks},null,2)}\n`,"utf8");
console.log(JSON.stringify({status:"PASS",records:validation.record_count,gallery:art.validation.gallery_count,aplus_modules:art.validation.aplus_module_count,aplus_units:art.validation.aplus_unit_count,p0_gaps:art.p0_asset_gaps.length,p1_gaps:art.p1_asset_gaps.length,score:art.quality.score.overall,workbooks:workbooks.map(item=>item.file)},null,2));
