package com.everyones.lawmaking.global.util;

import com.everyones.lawmaking.global.auth.PrincipalDetails;
import com.everyones.lawmaking.global.error.AuthException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.Optional;

public class AuthenticationUtil {

    public static Optional<Long> getUserId() {
        return getUserId(SecurityContextHolder.getContext().getAuthentication());
    }

    public static Optional<Long> getUserId(Authentication authentication) {
        if (authentication == null) {
            return Optional.empty();
        }

        Object principal = authentication.getPrincipal();
        if (principal instanceof UserDetails userDetails) {
            return usernameToUserId(userDetails.getUsername());
        }

        if (principal instanceof PrincipalDetails principalDetails) {
            return Optional.ofNullable(principalDetails.getUserId());
        }

        if (principal instanceof String principalName) {
            if ("anonymousUser".equals(principalName) || "anonymous".equals(principalName)) {
                return Optional.empty();
            }
            return usernameToUserId(principalName);
        }

        return Optional.empty();
    }

    public static Long requireUserId(Authentication authentication) {
        return getUserId(authentication).orElseThrow(AuthException.Unauthorized::new);
    }

    private static Optional<Long> usernameToUserId(String username) {
        try {
            return Optional.of(Long.parseLong(username));
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    private static boolean hasAuthority(Collection<? extends GrantedAuthority> authorities, String authority) {
        if (authorities == null) {
            return false;
        }

        for (GrantedAuthority grantedAuthority : authorities) {
            if (authority.equals(grantedAuthority.getAuthority())) {
                return true;
            }
        }
        return false;
    }
}
