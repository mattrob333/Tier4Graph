# CPE Graph Ontology

## Nodes
### Vendor
- vendor_id  
- name  
- summary  
- culture_embedding  
- risk_score  
- financial_stability  

### Facility
- facility_id  
- vendor_id  
- geo  
- tier  
- cooling  
- power_density  

### Service
- service_id  
- category  
- description  

### Certification
- cert_id  
- name  
- notes  

### Client
- client_id  
- industry  
- revenue  
- risk_tolerance  
- need_embedding  

### Project
- project_id  
- timeline  
- budget  
- go_live_date  

### Constraint
- type  
- description  
- parameters (JSON)  

## Relationships
- VENDOR OWNS FACILITY  
- FACILITY CONNECTED_TO CARRIER  
- CLIENT REQUIRES CONSTRAINT  
- CLIENT RATED VENDOR  
