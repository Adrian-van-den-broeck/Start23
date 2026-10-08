param([string]$PackagePath)
$ErrorActionPreference='Stop'
$sourceBook=[System.IO.Path]::GetFullPath((Join-Path $PackagePath 'WOMBO_Training_Simulator.xlsx'))
$testBook=[System.IO.Path]::GetFullPath((Join-Path $PackagePath 'qa\native-parity-copy.xlsx'))
Copy-Item -LiteralPath $sourceBook -Destination $testBook -Force
$cases=Get-Content -LiteralPath (Join-Path $PackagePath 'fixtures\parity_cases.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$excel=$null; $book=$null
$results=New-Object System.Collections.Generic.List[object]
try {
 $excel=New-Object -ComObject Excel.Application
 $excel.Visible=$false
 $excel.DisplayAlerts=$false
 $excel.AskToUpdateLinks=$false
 $excel.AutomationSecurity=3
 $book=$excel.Workbooks.Open($testBook,0,$false)
 $excel.CalculateFullRebuild()
 foreach($case in $cases) {
  $original=New-Object System.Collections.Generic.List[object]
  foreach($input in $case.inputs) {
   $cell=$book.Worksheets.Item($input.sheet).Range($input.cell)
   $original.Add([pscustomobject]@{sheet=$input.sheet;cell=$input.cell;formula=$cell.Formula;value=$cell.Value2;isFormula=$cell.HasFormula})
   if($null -eq $input.value) {$cell.ClearContents()} elseif($input.value -is [bool]) {$cell.Value2=[bool]$input.value} elseif($input.value -is [string]) {$cell.Value2=[string]$input.value} else {$cell.Value2=[double]$input.value}
  }
  $excel.CalculateFullRebuild()
  foreach($expected in $case.expected) {
   $cell=$book.Worksheets.Item($expected.sheet).Range($expected.cell)
   $actual=$cell.Value2
   if($expected.value -is [string]) {$passed=([string]$actual -ceq [string]$expected.value);$difference=$null} else {
    $difference=if($actual -is [double] -or $actual -is [int]) {[double]$actual-[double]$expected.value} else {$null}
    $passed=$null -ne $difference -and [Math]::Abs($difference) -le 1e-9
   }
   $results.Add([pscustomobject]@{case=$case.id;rule=$case.rule;sheet=$expected.sheet;cell=$expected.cell;expected=$expected.value;actual=$actual;difference=$difference;passed=[bool]$passed})
  }
  foreach($saved in $original) {
   $cell=$book.Worksheets.Item($saved.sheet).Range($saved.cell)
   if($saved.isFormula) {$cell.Formula=$saved.formula} elseif($null -eq $saved.value) {$cell.ClearContents()} elseif($saved.value -is [bool]) {$cell.Value2=[bool]$saved.value} elseif($saved.value -is [string]) {$cell.Value2=[string]$saved.value} else {$cell.Value2=[double]$saved.value}
  }
 }
 $excel.CalculateFullRebuild()
 $errors=New-Object System.Collections.Generic.List[object]
 foreach($sheet in $book.Worksheets) {
  try {$range=$sheet.UsedRange.SpecialCells(-4123,16)} catch {$range=$null}
  if($null -ne $range) {foreach($cell in $range.Cells) {$errors.Add([pscustomobject]@{sheet=$sheet.Name;cell=$cell.Address();text=$cell.Text})}}
 }
 $report=[pscustomobject]@{source_sha='6b1189b70a6505726fef70c4616a2f3d6dd4c94a';run_utc=[DateTime]::UtcNow.ToString('o');excel_version=$excel.Version;cases=$cases.Count;assertions=$results.Count;passed=@($results | Where-Object passed).Count;failed=@($results | Where-Object { -not $_.passed }).Count;formula_errors=$errors;results=$results;full_engine_verified=$false}
 $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PackagePath 'qa\native-parity-results.json') -Encoding UTF8
 $book.Close($false);$book=$null
 # Recalculate and save only the newly authored handoff workbook after tests.
 $book=$excel.Workbooks.Open($sourceBook,0,$false)
 $excel.CalculateFullRebuild()
 $paritySheet=$book.Worksheets.Item('27_PARITY_RESULTS')
 $paritySheet.Range('B6').Value2=[string]($report.passed.ToString()+'/'+$report.assertions.ToString()+' assertions PASS; '+$report.cases.ToString()+' scenarios')
 $paritySheet.Range('C6').Value2='Alleen geteste berekeningen; volledige engine INCOMPLETE'
 $book.Save()
 Write-Output ('Excel ' + $report.excel_version + ': ' + $report.cases + ' scenarios; ' + $report.passed + '/' + $report.assertions + ' assertions passed; formula errors=' + $errors.Count)
 if($report.failed -gt 0 -or $errors.Count -gt 0){throw 'Native Excel parity verification failed; inspect qa/native-parity-results.json'}
} finally {
 if($null -ne $book) {$book.Close($false)}
 if($null -ne $excel) {$excel.Quit();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel) | Out-Null}
}
