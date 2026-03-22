package com.everyones.lawmaking.global.util;

import java.util.List;

public class PaginationUtil {

    public static <T> boolean hasNextPage(List<T> contents, int pageSize) {
        if(contents.size() > pageSize) {
            contents.remove(pageSize);
            return false;
        }
        return true;
    }

}
