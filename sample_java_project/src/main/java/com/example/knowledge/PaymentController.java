package com.example.knowledge;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    /**
     * Executes payment processing. Undocumented endpoint.
     */
    @PostMapping("/process")
    public String processPayment(@RequestBody String paymentInfo) {
        return "Payment transaction processed";
    }
}
