package com.example.coder;
import java.util.Map;
import org.springframework.web.bind.annotation.*;
@RestController
public class ApprovalController {
 private final ApprovalService approvals;
 public ApprovalController(ApprovalService approvals){this.approvals=approvals;}
 @PostMapping("/api/approvals/{taskId}")
 public Map<String,String> approve(@PathVariable String taskId){
  // Demo only. Production: authenticate an authorized reviewer.
  return Map.of("approval_token",approvals.create(taskId),"expires_in","1800s");
 }
}