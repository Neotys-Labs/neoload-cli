# Bamboo Pipeline Examples
These examples demonstrate how the NeoLoad CLI simplifies the syntax required to
 execute load tests from within a Bamboo pipeline.

## TL;DR
 - Create a **bamboo project**. Initials "PT"
 - Set values for the 3 variables in *bamboo.yaml* : 'api_url', 'token_secret' and 'zone_id'
 - Push *bamboo.yaml* to your Neoload project repository
 - Setup Spec Repository in Bamboo and link the repository

## How to
 - In Bamboo, create a project from the top menu *Create* with initials "PT". These initials are the *project key* in bamboo.yaml.
 - In your repository, create the file bamboo.yaml in the folder bamboo-specs.
  This folder must be at the **root of the repository**
 - Paste the content of either *bamboo-v1.yaml* or *bamboo-v2.yaml* in your bamboo.yaml and push it to your repository.

   - **bamboo-v1.yaml works since Bamboo 6.3**<br>
    In bamboo-v1.yaml, replace these 3 placeholders with your own values :
      - *<api_url>* &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Example: https://neoload-api.saas.neotys.com
      - *<token_secret>* &nbsp;&nbsp;&nbsp;&nbsp; Your NLWeb API token
      - *<zone_id>* &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Example: defaultzone
   - **bamboo-v2.yaml works since Bamboo 6.9**<br>
    In bamboo-v2.yaml, replace the 3 variables with your own values :
      - *api_url* &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Example: https://neoload-api.saas.neotys.com
      - *token_secret* &nbsp;&nbsp;&nbsp;&nbsp; Your NLWeb API token. It must be encrypted with Bamboo spec encryption tool
      - *zone_id* &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Example: defaultzone
 
 - In Bamboo menu Specs > Setup Spec Repository, link the project to your repository (check "Link new repository").
 
 The pipeline should start and will run your performance test !
 
> To update the yaml file, push the updated bamboo.yaml on git and reload it in Bamboo :<br>
> Settings > Linked Repositories > Choose the repository > Spec status : click on "Scan" button.

## SLA Reporting via JUnit
The job will display sla results in Tests tab and will fail if one SLA fails, and succeed if no SLA is broken.<br>
<img src="Bamboo_Pipeline_NeoLoad_SLA_jUnit.jpg">
