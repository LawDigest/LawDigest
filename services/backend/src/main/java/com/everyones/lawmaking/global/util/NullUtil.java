package com.everyones.lawmaking.global.util;

import java.util.function.Supplier;

public class NullUtil {

    public static <T> T nullCoalescing(Supplier<T> dataGetter, T defaultValue) {
        try {
            T value = dataGetter.get();
            return value != null ? value : defaultValue;
        } catch (NullPointerException e) {
            return defaultValue;
        }
    }
}
