$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#product_id").val(res.id);
        $("#product_name").val(res.name);
        $("#product_category").val(res.category);
        $("#product_price").val(res.price);
        $("#product_stock").val(res.stock);
        $("#product_description").val(res.description);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#product_name").val("");
        $("#product_category").val("");
        // $("#product_available").val("");
        $("#product_price").val("");
        $("#product_stock").val("");
        $("#product_description").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Product
    // ****************************************

    $("#create-btn").click(function () {

        let name       = $("#product_name").val();
        let category   = $("#product_category").val();
        // let available  = $("#product_available").val() == "true";
        let price      = $("#product_price").val();
        let stock      = $("#product_stock").val();
        let description= $("#product_description").val();

        let data = {
            "name": name,
            "category": category,
            // "available": available,
            "price" : price,
            "stock" : stock,
            "description" : description
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: "/products",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // ****************************************
    // Update a Product
    // ****************************************

    $("#update-btn").click(function () {

        let product_id = $("#product_id").val();
        let name       = $("#product_name").val();
        let category   = $("#product_category").val();
        // let available  = $("#product_available").val() == "true";
        let price      = $("#product_price").val();
        let stock      = $("#product_stock").val();
        let description= $("#product_description").val();

        let data = {
            "name": name,
            "category": category,
            // "available": available,
            "price" : price,
            "stock" : stock,
            "description" : description
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/products/${product_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Product
    // ****************************************

    $("#retrieve-btn").click(function () {

        let product_id = $("#product_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/products/${product_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            // alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Product
    // ****************************************

    $("#delete-btn").click(function () {

        let product_id = $("#product_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/products/${product_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Product has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#product_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for a Product
    // ****************************************

    $("#search-btn").click(function () {

        let name      = $("#product_name").val();
        let category  = $("#product_category").val();
        // let available = $("#product_available").val() == "true";

        let queryString = ""

        if (name) {
            queryString += 'name=' + name
        }
        if (category) {
            if (queryString.length > 0) {
                queryString += '&category=' + category
            } else {
                queryString += 'category=' + category
            }
        }
        // if (available) {
        //     if (queryString.length > 0) {
        //         queryString += '&available=' + available
        //     } else {
        //         queryString += 'available=' + available
        //     }
        // }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/products?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">ID</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Category</th>'
            table += '<th class="col-md-2">Price</th>'
            table += '<th class="col-md-2">Stock</th>'
            table += '<th class="col-md-4">Description</th>'
            table += '</tr></thead><tbody>'
            let firstProduct = "";
            for(let i = 0; i < res.length; i++) {
                let product = res[i];
                // console.log(product);
                table +=  `<tr id="row_${i}"><td>${product.id}</td><td>${product.name}</td><td>${product.category}</td><td>${product.price}</td><td>${product.stock}</td><td>${product.description}</td></tr>`;
                if (i == 0) {
                    firstProduct= product;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstProduct != "") {
                update_form_data(firstProduct)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

})
