import assert from "node:assert/strict";
import fs from "node:fs";
import { buildArtDirectionSpec, validateArtDirectionSpec } from "../scripts/art_direction_system.mjs";
import { buildProductSemanticContext } from "../scripts/product_semantic_context.mjs";

const specPath=process.argv[2];
if(!specPath) throw new Error("Pass Lock PRODUCT_PAGE_SPEC.json path");
const spec=JSON.parse(fs.readFileSync(specPath,"utf8"));
const clean=buildArtDirectionSpec(spec);
assert.equal(validateArtDirectionSpec(clean).status,"PASS");
assert.equal(clean.semantic_contamination.status,"PASS");

const forbidden=buildProductSemanticContext(spec).category_semantics.forbidden_cross_product_semantics;
for(const term of forbidden){
  const injected=structuredClone(clean);
  injected.gallery[1].visual_objective=`Injected cross-product term: ${term}`;
  const result=validateArtDirectionSpec(injected);
  assert.equal(result.status,"FAIL",`term should fail: ${term}`);
  assert.equal(result.semantic_relevance.code,"CROSS_PRODUCT_SEMANTIC_CONTAMINATION");
  assert.ok(result.semantic_relevance.hit_count>0,`term should be detected: ${term}`);
}

const genericSpec={
  meta:{spec_sha256:"generic"},
  product:{name:"SwitchBot Generic Device",category:"generic connected device",sku:"NA"},
  story_sequence_lock:{fingerprint:"generic"},
  product_images:[{id:"IMAGE-01",sequence:1,stage:"understand",role:"Identity",template_id:"P-MAIN-OFFICIAL",headline:"",claim_ids:[],claim_source:"NA",status:"Need Verification"}],
  aplus_modules:[],claims:[],reference_selection:{},
};
const generic=buildArtDirectionSpec(genericSpec);
assert.equal(validateArtDirectionSpec(generic).status,"PASS");
const injectedLock=structuredClone(generic);
injectedLock.gallery[0].visual_objective="Injected smart lock content";
const genericResult=validateArtDirectionSpec(injectedLock);
assert.equal(genericResult.status,"FAIL");
assert.equal(genericResult.semantic_relevance.code,"CROSS_PRODUCT_SEMANTIC_CONTAMINATION");

console.log(JSON.stringify({status:"PASS",clean_records:clean.validation.record_count,forbidden_terms_tested:forbidden.length,generic_cross_product_guard:"PASS"},null,2));
