package com.example.coder;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.method.MethodToolCallbackProvider;
@SpringBootApplication
public class CodingToolsApplication {
 public static void main(String[] args){SpringApplication.run(CodingToolsApplication.class,args);}
 @Bean ToolCallbackProvider tools(WorkspaceTools t){
  return MethodToolCallbackProvider.builder().toolObjects(t).build();
 }
}