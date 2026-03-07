Write-Host ===============================================
Write-Host AI_DOCUMENT_AGENT_FULL_TEST_SUITE
Write-Host ===============================================

function Run-Test($question) {

    Write-Host ""
    Write-Host -----------------------------------------------
    Write-Host QUESTION
    Write-Host $question
    Write-Host -----------------------------------------------

    $body = @{
        question = $question
    } | ConvertTo-Json

    $resp = Invoke-RestMethod -Uri http://localhost:8000/api/v1/query `
                              -Method POST `
                              -Body $body `
                              -ContentType application/json

    $resp.answer | Out-File response.txt -Encoding utf8
    notepad response.txt
}

############################################################
# DOCUMENT DISCOVERY
############################################################

Run-Test "Please share whatever the document list you have"
Run-Test "Share all the documents metadata list"
Run-Test "What documents are available in the system"

############################################################
# DOCUMENT DOWNLOAD
############################################################

Run-Test "Share download link for Aishiki_Reliable_Poushali_2025_Gyano.pdf"
Run-Test "Download the file Sem-1.pdf"
Run-Test "Provide the download link for Sem-3.pdf"
Run-Test "Download link for TCS Latest Increment Letter.pdf"

############################################################
# DOCUMENT ID DOWNLOAD
############################################################

Run-Test "Download document with id 3e91f6c9-642f-415a-bfb8-2d3cff0a9b61"

############################################################
# MEDICAL DOCUMENT
############################################################

Run-Test "What medicine was prescribed by Doctor Poushali for Aishiki"
Run-Test "Share SOS medicine mentioned in Reliable diagnostic prescription for Aishiki"
Run-Test "Provide details from Aishiki Reliable prescription document"

############################################################
# SEMESTER DOCUMENT
############################################################

Run-Test "Share details from Sem-1.pdf"
Run-Test "Give download link for Sem-1.pdf"
Run-Test "Show semester 1 document content and provide download link"
Run-Test "I want to understand my semester 3 results"
Run-Test "Which semester has lowest SGPA for Rajat"

############################################################
# FINANCIAL DOCUMENT
############################################################

Run-Test "Share top 3 transactions from HSBC statement"
Run-Test "Latest 3 HSBC transactions"
Run-Test "Show HSBC statement details"

############################################################
# INSURANCE DOCUMENT
############################################################

Run-Test "Share insurance details for vehicle registration WB02AK5172"
Run-Test "Vehicle insurance policy details for car WB02AK5172"

############################################################
# EMPLOYMENT DOCUMENT
############################################################

Run-Test "Summarize TCS offer letter"
Run-Test "Share details from TCS Latest Increment Letter"

############################################################
# ID DOCUMENT
############################################################

Run-Test "Show passport details"
Run-Test "Share PAN card details"

############################################################
# COMPLEX QUERIES
############################################################

Run-Test "Find semester document where Rajat got lowest SGPA and give download link"
Run-Test "Show HSBC transactions and allow download of statement"
Run-Test "Find insurance policy document and provide download link"

############################################################
# EDGE CASES
############################################################

Run-Test "Sem-1"
Run-Test "WB02AK5172"
Run-Test "HSBC"
Run-Test "Insurance"
Run-Test "Prescription"

Write-Host ""
Write-Host ===============================================
Write-Host ALL_TESTS_COMPLETED
Write-Host ===============================================