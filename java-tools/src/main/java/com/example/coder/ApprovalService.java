package com.example.coder;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;
@Service
public class ApprovalService {
 record Approval(String token,String taskId,Instant expiresAt){}
 private final ConcurrentHashMap<String,Approval> map=new ConcurrentHashMap<>();
 public String create(String taskId){
  String token=UUID.randomUUID().toString();
  map.put(token,new Approval(token,taskId,Instant.now().plusSeconds(1800)));return token;
 }
 public boolean valid(String token,String taskId){
  Approval a=map.get(token);
  return a!=null&&a.taskId().equals(taskId)&&Instant.now().isBefore(a.expiresAt());
 }
}