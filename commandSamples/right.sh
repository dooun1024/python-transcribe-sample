# 查看现在的
aws iam list-attached-role-policies --role-name mc11-role-wfaeuzkd

# 
aws iam put-role-policy --role-name mc11-role-wfaeuzkd --policy-name TranscribeS3Policy --policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"transcribe:StartTranscriptionJob\",\"transcribe:GetTranscriptionJob\"],\"Resource\":\"*\"},{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\",\"s3:PutObject\"],\"Resource\":[\"arn:aws:s3:::ka-test-bucket-11/*\",\"arn:aws:s3:::ka-test-bucket-12/*\"]}]}"

# 验证policy
aws iam get-role-policy --role-name mc11-role-wfaeuzkd --policy-name TranscribeS3Policy

