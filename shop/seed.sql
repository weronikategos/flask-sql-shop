INSERT INTO categories (name) VALUES ('Coffee'), ('Tea'), ('Accessories');

INSERT INTO products (category_id, name, description, price, stock) VALUES
    (1, 'Brazil whole bean coffee 250 g', 'Chocolatey, low acidity', 39.99, 25),
    (1, 'Ethiopia whole bean coffee 250 g', 'Fruity, light roast', 49.99, 15),
    (1, 'Colombia ground coffee 250 g', 'For drip coffee makers', 34.99, 30),
    (2, 'Sencha green tea 100 g', 'Japanese, loose leaf', 29.99, 40),
    (2, 'Assam black tea 100 g', 'Strong and malty', 24.99, 35),
    (3, 'V60 dripper', 'Ceramic, size 02', 89.00, 10),
    (3, 'Hand coffee grinder', 'Steel burrs, adjustable grind size', 149.00, 5),
    (3, 'Travel mug 350 ml', 'Stainless steel', 59.00, 20);
