# Architecture Summary (Week 4)

## What this system does
Music Soulmate Finder is a serverless backend that:
1) builds a user taste profile (artists/genres/tracks)
2) stores profiles in DynamoDB
3) returns ranked matches for a user based on similarity

## AWS components
- API Gateway (HTTP API): receives requests from a client
- Lambda (Python): runs taste profile + match logic
- DynamoDB: stores user profiles by `user_id`
- CloudWatch Logs: debugging and proof

## Data flow (request path)

Client  
  ↓  
API Gateway  
  ↓  
Lambda  
  ↓  
DynamoDB
