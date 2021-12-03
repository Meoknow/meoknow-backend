const admin_update_cat_api_url = "/admin/update_cat_api";
const admin_delete_cat_api_url = "/admin/delete_cat_api";
const admin_add_cat_api_url = "/admin/add_cat_api";
const admin_get_cats_api_url = "/admin/get_cats_api";
const admin_get_comments_api_url = "/admin/get_comments_api";
const admin_get_comments_by_cat_url = "/admin/get_comments_by_cat_api";
const admin_get_comment_url = "/admin/get_comment_api";
const admin_hide_comment_api_url = "/admin/hide_comment_api";
const admin_show_comment_api_url = "/admin/show_comment_api";

function admin_post_api(url, payload) {
    return new Promise((res, rej) => {
        $.ajax({
            type: "POST",
            url: url,
            data: JSON.stringify(payload),
            contentType: "application/json",
            success(e) {
                if (e.code === 0) res(e.data);
                else rej(e.msg || "failed");
            },
            error() {
                rej("failed");
            },
        });
    });
}

function admin_get_api(url, payload) {
    return new Promise((res, rej) => {
        $.ajax({
            type: "GET",
            url: url,
            data: payload,
            success(e) {
                if (e.code === 0) res(e.data);
                else rej(e.msg || "failed");
            },
            error() {
                rej("failed");
            },
        });
    });
}

function admin_update_cat_api(payload) {
    return admin_post_api(
        admin_update_cat_api_url,
        payload
    );
}

function admin_delete_cat_api(cat_id) {
    return admin_post_api(
        admin_delete_cat_api_url,
        {cat_id: cat_id}
    );
}

function admin_add_cat_api(payload) {
    return admin_post_api(
        admin_add_cat_api_url,
        payload
    );
}

function admin_get_cats_api(page) {
    return admin_get_api(
        admin_get_cats_api_url,
        {page: page}
    );
}

function admin_get_comments_by_cat_api(cat_id, page) {
    return admin_get_api(
        admin_get_comments_by_cat_url,
        {cat_id: cat_id, page: page}
    );
}

function admin_get_comments_api(page) {
    return admin_get_api(
        admin_get_comments_api_url,
        {page: page}
    );
}

function admin_get_comment_api(comment_id) {
    return admin_get_api(
        admin_get_comment_url,
        {comment_id: comment_id}
    );
}

function admin_hide_comment_api(comment_id) {
    return admin_post_api(
        admin_hide_comment_api_url,
        {comment_id: comment_id}
    );
}

function admin_show_comment_api(comment_id) {
    return admin_post_api(
        admin_show_comment_api_url,
        {comment_id: comment_id}
    );
}