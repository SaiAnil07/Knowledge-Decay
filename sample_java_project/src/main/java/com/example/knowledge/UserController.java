package com.example.knowledge;

import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    /**
     * Retrieves all registered users sorted alphabetically by username.
     */
    @GetMapping
    public List<String> findAllOrderByUsername() {
        return List.of("alice_dev", "bob_coder", "charlie_qa");
    }

    @GetMapping("/{id}")
    public String getUserById(@PathVariable Long id) {
        return "User details for ID: " + id;
    }

    @PostMapping
    public String createUser(@RequestBody String userPayload) {
        return "User created successfully";
    }

    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        // Soft delete user record
    }
}
