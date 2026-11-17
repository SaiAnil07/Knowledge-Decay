package com.example.knowledge;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    /**
     * Submits and creates a new customer order. Requires POST HTTP method.
     */
    @PostMapping
    public String createOrder(@RequestBody String orderJson) {
        return "Order submitted successfully";
    }

    @GetMapping("/{orderId}")
    public String getOrderDetails(@PathVariable String orderId) {
        return "Order status for: " + orderId;
    }
}
